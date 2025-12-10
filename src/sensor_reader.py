"""
Main Sensor Reader Service
Reads BACnet sensors and manages data flow to API
Compatible with BAC0 2025.9.15 and Python 3.13
"""

import asyncio
import time
import signal
import sys
from datetime import datetime
from typing import List, Dict, Optional

try:
    import BAC0

    BAC0_AVAILABLE = True
except ImportError:
    BAC0_AVAILABLE = False
    print("Warning: BAC0 not installed. Run: pip install BAC0")

from src.config import Config
from src.logger import setup_logger
from src.database import Database
from src.api_client import APIClient

logger = setup_logger(__name__)


class SensorReader:
    """Main service for reading sensors and managing data"""

    def __init__(self):
        self.bacnet = None
        self.device = None
        self.database = Database()
        self.api_client = APIClient()
        self.running = False
        self.last_post_time = 0

        # Register signal handlers for graceful shutdown
        signal.signal(signal.SIGINT, self.signal_handler)
        signal.signal(signal.SIGTERM, self.signal_handler)

    def signal_handler(self, signum, frame):
        """Handle shutdown signals"""
        logger.info(f"Received signal {signum}, shutting down gracefully...")
        self.running = False

    async def connect_bacnet(self) -> bool:
        """
        Connect to BACnet network

        Returns:
            True if successful
        """
        if not BAC0_AVAILABLE:
            logger.error("BAC0 library not available")
            return False

        try:
            logger.info(f"Connecting to BACnet network: {Config.BACNET_IP}:{Config.BACNET_PORT}")

            # BAC0 2025.x - use start() without await
            self.bacnet = BAC0.start(ip=Config.BACNET_IP, port=Config.BACNET_PORT)

            logger.info("✓ Connected to BACnet network")

            # Wait for network to stabilize
            await asyncio.sleep(2)

            # Try to connect to the target device
            target_address = f"{Config.TARGET_DEVICE_IP}:{Config.BACNET_TARGET_PORT}"
            logger.info(f"Connecting to device at {target_address} (ID: {Config.TARGET_DEVICE_ID})...")

            try:
                # BAC0.device() must be awaited
                self.device = await BAC0.device(
                    target_address,
                    Config.TARGET_DEVICE_ID,
                    self.bacnet
                )

                logger.info(f"✓ Connected to device: {self.device.properties.name}")
                logger.info(f"Available points on device:")
                for point in self.device.points:
                    logger.info(f"  - {point.properties.name} ({point.properties.type})")

                return True

            except Exception as e:
                logger.warning(f"Could not create device object: {e}")
                logger.info("Will attempt direct reads instead")
                return True

        except Exception as e:
            logger.error(f"Failed to connect to BACnet: {e}", exc_info=True)
            return False

    async def read_sensors(self) -> List[Dict]:
        """
        Read all configured sensors

        Returns:
            List of sensor readings
        """
        readings = []
        timestamp = datetime.now().isoformat()
        sensors = Config.get_sensor_config()

        if not self.bacnet:
            logger.warning("BACnet not connected, skipping read")
            return readings

        for sensor in sensors:
            try:
                # Try reading via device object first (if available)
                if self.device:
                    try:
                        point = self.device[sensor['name']]
                        value = await point.value

                        if value is not None:
                            reading = {
                                'timestamp': timestamp,
                                'sensor_name': sensor['name'],
                                'value': float(value),
                                'unit': sensor['unit'],
                                'priority_array': None,
                                'active_priority': None
                            }

                            # Try to read priority array and active priority
                            # Only commandable objects have priority arrays (analogValue, analogOutput, binaryValue, binaryOutput, etc.)
                            obj_type, obj_instance = sensor['object'].split(':')
                            commandable_types = ['analogValue', 'analogOutput', 'binaryValue', 'binaryOutput', 'multiStateValue', 'multiStateOutput']

                            if obj_type in commandable_types:
                                try:
                                    target_address = f"{Config.TARGET_DEVICE_IP}:{Config.BACNET_TARGET_PORT}"

                                    # Read priority array (property 87)
                                    priority_array_point = f"{target_address} {obj_type} {obj_instance} priorityArray"
                                    priority_array = await self.bacnet.read(priority_array_point)
                                    if priority_array is not None and not isinstance(priority_array, str):
                                        # Convert to list, handling various return types
                                        if hasattr(priority_array, '__iter__'):
                                            pa_list = []
                                            for v in priority_array:
                                                try:
                                                    if v is None or (hasattr(v, 'is_null') and v.is_null) or str(v).lower() == 'null':
                                                        pa_list.append(None)
                                                    else:
                                                        pa_list.append(float(v))
                                                except (ValueError, TypeError):
                                                    pa_list.append(None)
                                            reading['priority_array'] = pa_list
                                        else:
                                            reading['priority_array'] = priority_array

                                    # Determine active priority from priority array
                                    if reading['priority_array'] and isinstance(reading['priority_array'], list):
                                        # Find the highest priority (lowest index) with a non-null value
                                        for idx, prio_value in enumerate(reading['priority_array']):
                                            if prio_value is not None:
                                                reading['active_priority'] = idx + 1  # BACnet priorities are 1-indexed
                                                break

                                except Exception as prio_e:
                                    logger.debug(f"Could not read priority info for {sensor['name']}: {prio_e}")

                            readings.append(reading)
                            logger.debug(f"✓ {sensor['name']}: {value} {sensor['unit']} (priority: {reading['active_priority']})")
                        continue
                    except Exception as e:
                        logger.debug(f"Device read failed for {sensor['name']}, trying direct read: {e}")

                # Fallback to direct read
                target_address = f"{Config.TARGET_DEVICE_IP}:{Config.BACNET_TARGET_PORT}"
                obj_type, obj_instance = sensor['object'].split(':')
                bacnet_point = f"{target_address} {obj_type} {obj_instance} presentValue"

                # BAC0 2025.x - read() is async
                value = await self.bacnet.read(bacnet_point)

                if value is not None:
                    reading = {
                        'timestamp': timestamp,
                        'sensor_name': sensor['name'],
                        'value': float(value),
                        'unit': sensor['unit'],
                        'priority_array': None,
                        'active_priority': None
                    }

                    # Try to read priority array and active priority
                    # Only commandable objects have priority arrays
                    commandable_types = ['analogValue', 'analogOutput', 'binaryValue', 'binaryOutput', 'multiStateValue', 'multiStateOutput']

                    if obj_type in commandable_types:
                        try:
                            # Read priority array (property 87)
                            priority_array_point = f"{target_address} {obj_type} {obj_instance} priorityArray"
                            priority_array = await self.bacnet.read(priority_array_point)
                            if priority_array is not None and not isinstance(priority_array, str):
                                # Convert to list, handling various return types
                                if hasattr(priority_array, '__iter__'):
                                    pa_list = []
                                    for v in priority_array:
                                        try:
                                            if v is None or (hasattr(v, 'is_null') and v.is_null) or str(v).lower() == 'null':
                                                pa_list.append(None)
                                            else:
                                                pa_list.append(float(v))
                                        except (ValueError, TypeError):
                                            pa_list.append(None)
                                    reading['priority_array'] = pa_list
                                else:
                                    reading['priority_array'] = priority_array

                            # Determine active priority from priority array
                            if reading['priority_array'] and isinstance(reading['priority_array'], list):
                                # Find the highest priority (lowest index) with a non-null value
                                for idx, prio_value in enumerate(reading['priority_array']):
                                    if prio_value is not None:
                                        reading['active_priority'] = idx + 1  # BACnet priorities are 1-indexed
                                        break

                        except Exception as prio_e:
                            logger.debug(f"Could not read priority info for {sensor['name']}: {prio_e}")

                    readings.append(reading)
                    logger.debug(f"✓ {sensor['name']}: {value} {sensor['unit']} (priority: {reading['active_priority']})")
                else:
                    logger.warning(f"✗ {sensor['name']}: No response")

            except Exception as e:
                logger.error(f"✗ Failed to read {sensor['name']}: {e}")

        if readings:
            logger.info(f"Read {len(readings)}/{len(sensors)} sensor values")
        else:
            logger.warning("No sensors responded")

        return readings

    def simulate_readings(self) -> List[Dict]:
        """
        Simulate sensor readings for testing without BACnet

        Returns:
            List of simulated readings
        """
        import random

        readings = []
        timestamp = datetime.now().isoformat()

        simulated_data = {
            'Temperature': (20.0, 30.0, 'degreesCelsius'),
            'Humidity': (40.0, 60.0, 'percent'),
            'Pressure': (100.0, 102.0, 'kilopascals'),
        }

        for sensor_name, (min_val, max_val, unit) in simulated_data.items():
            value = random.uniform(min_val, max_val)
            # Simulate priority array (16 levels, mostly null)
            priority_array = [None] * 16
            active_priority = random.choice([8, 10, 12, 16])  # Common BACnet priority levels
            priority_array[active_priority - 1] = round(value, 2)

            readings.append({
                'timestamp': timestamp,
                'sensor_name': sensor_name,
                'value': round(value, 2),
                'unit': unit,
                'priority_array': priority_array,
                'active_priority': active_priority
            })

        logger.debug(f"Generated {len(readings)} simulated readings")
        return readings

    async def process_readings(self):
        """Read sensors and store locally"""
        if Config.SIMULATE_MODE or not self.bacnet:
            readings = self.simulate_readings()
        else:
            readings = await self.read_sensors()

        if readings:
            self.database.store_readings(readings)

    def sync_with_api(self):
        """Post unposted readings to API"""
        unposted = self.database.get_unposted_readings()

        if not unposted:
            logger.debug("No readings to sync")
            return

        # Prepare readings for API (remove IDs)
        readings_for_api = [{
            'timestamp': r['timestamp'],
            'sensor_name': r['sensor_name'],
            'value': r['value'],
            'unit': r['unit'],
            'priority_array': r.get('priority_array'),
            'active_priority': r.get('active_priority')
        } for r in unposted]

        # Post to API
        if self.api_client.post_sensor_data(readings_for_api):
            # Mark as posted
            reading_ids = [r['id'] for r in unposted]
            self.database.mark_as_posted(reading_ids)

            # Cleanup old data
            self.database.cleanup_old_data(days=7)
        else:
            logger.warning("Failed to post to API, will retry later")

    async def run_async(self):
        """Async main service loop"""
        logger.info("=" * 60)
        logger.info("Heitz - Sensor Reader Service")
        logger.info("=" * 60)
        logger.info(f"Device ID: {Config.DEVICE_NAME}")
        logger.info(f"API URL: {Config.API_URL}")
        logger.info(f"Read Interval: {Config.READ_INTERVAL}s")
        logger.info(f"Post Interval: {Config.POST_INTERVAL}s")
        logger.info(f"Simulate Mode: {Config.SIMULATE_MODE}")
        logger.info(f"Python Version: {sys.version}")
        if BAC0_AVAILABLE:
            version = getattr(BAC0, "__version__", "unknown")
            logger.info(f"BAC0 Version: {version}")
        logger.info("=" * 60)

        # Validate configuration
        try:
            Config.validate()
        except ValueError as e:
            logger.error(f"Configuration error: {e}")
            return

        # Check API connectivity
        if not self.api_client.health_check():
            logger.warning("⚠ Cannot reach API server, will continue and retry later")
        else:
            logger.info("✓ API server is reachable")

        # Connect to BACnet if not in simulate mode
        if not Config.SIMULATE_MODE:
            if not await self.connect_bacnet():
                logger.error("Cannot start: BACnet connection failed")
                logger.info("Hint: Set SIMULATE_MODE=True in .env to test without BACnet")
                return
        else:
            logger.info("Running in SIMULATION mode (no real BACnet connection)")

        # Main loop
        self.running = True
        logger.info("✓ Service started successfully")
        logger.info("")

        try:
            while self.running:
                cycle_start = time.time()

                # Read sensors
                await self.process_readings()

                # Sync with API if interval elapsed
                if time.time() - self.last_post_time >= Config.POST_INTERVAL:
                    self.sync_with_api()
                    self.last_post_time = time.time()

                    # Show stats
                    stats = self.database.get_stats()
                    logger.info(f"📊 Stats: {stats['total_readings']} total, "
                                f"{stats['unposted_readings']} pending")

                # Wait for next cycle
                elapsed = time.time() - cycle_start
                sleep_time = max(0, Config.READ_INTERVAL - elapsed)

                if sleep_time > 0:
                    await asyncio.sleep(sleep_time)

        except KeyboardInterrupt:
            logger.info("Service stopped by user")
        except Exception as e:
            logger.error(f"Unexpected error: {e}", exc_info=True)
        finally:
            await self.shutdown()

    async def shutdown(self):
        """Clean shutdown"""
        logger.info("\n" + "=" * 60)
        logger.info("Shutting down...")

        # Try to post any remaining data
        try:
            self.sync_with_api()
        except:
            pass

        # Close connections
        if self.bacnet:
            try:
                await self.bacnet._disconnect()
                logger.info("✓ BACnet disconnected")
            except:
                pass

        self.database.close()
        self.api_client.close()
        logger.info("✓ Shutdown complete")
        logger.info("=" * 60)

    def run(self):
        """Entry point - runs async event loop"""
        asyncio.run(self.run_async())


def main():
    """Entry point"""
    reader = SensorReader()
    reader.run()


if __name__ == "__main__":
    main()
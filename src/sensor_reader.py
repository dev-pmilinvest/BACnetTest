#!/usr/bin/env python3
"""
Raspberry Pi BACnet Reader Service
Reads sensor values, stores locally, and posts to Laravel API
"""

import BAC0
import json
import sqlite3
import requests
import time
import logging
from datetime import datetime
from pathlib import Path

# Configuration
CONFIG = {
    'api_url': 'http://hiecoconso.test/api/sensor-data',
    'api_token': '1|uOf2HYlFTFcJJ2HJkhMaHoif8jlTzl37ilGId2WIbd6b5821',
    # 'bacnet_ip': '192.168.1.200/24',  # Pi's IP address
    'bacnet_ip': '127.0.0.1/24',
    'target_device_ip': '192.168.1.100',  # BACnet device IP
    'target_device_id': 100,
    'read_interval': 30,  # seconds between readings
    'post_interval': 300,  # seconds between API posts (5 min)
    'db_path': 'data/sensor_data.db'
}

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/reader.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class SensorReader:
    def __init__(self):
        self.bacnet = None
        self.db_conn = None
        self.init_database()

    def init_database(self):
        """Initialize SQLite database for local storage"""
        Path(CONFIG['db_path']).parent.mkdir(parents=True, exist_ok=True)
        self.db_conn = sqlite3.connect(CONFIG['db_path'])
        cursor = self.db_conn.cursor()

        cursor.execute('''
                       CREATE TABLE IF NOT EXISTS sensor_readings
                       (
                           id
                           INTEGER
                           PRIMARY
                           KEY
                           AUTOINCREMENT,
                           timestamp
                           TEXT
                           NOT
                           NULL,
                           sensor_name
                           TEXT
                           NOT
                           NULL,
                           value
                           REAL
                           NOT
                           NULL,
                           unit
                           TEXT,
                           posted
                           INTEGER
                           DEFAULT
                           0
                       )
                       ''')
        self.db_conn.commit()
        logger.info("Database initialized")

    def connect_bacnet(self):
        """Connect to BACnet network"""
        try:
            self.bacnet = BAC0.lite(ip=CONFIG['bacnet_ip'])
            logger.info(f"Connected to BACnet network: {CONFIG['bacnet_ip']}")
            return True
        except Exception as e:
            logger.error(f"Failed to connect to BACnet: {e}")
            return False

    def read_sensors(self):
        """Read sensor values from BACnet device"""
        readings = []
        timestamp = datetime.now().isoformat()

        try:
            # Discover device
            device_address = f"{CONFIG['target_device_ip']}:{CONFIG['target_device_id']}"

            # Define sensors to read (adjust based on your actual BACnet points)
            sensors = [
                {'name': 'pool_temperature', 'object': 'analogInput:1'},
                {'name': 'pool_ph', 'object': 'analogInput:2'},
                {'name': 'chlorine_level', 'object': 'analogInput:3'},
                {'name': 'water_pressure', 'object': 'analogInput:4'},
                {'name': 'flow_rate', 'object': 'analogInput:5'},
            ]

            for sensor in sensors:
                try:
                    # Read present value from BACnet object
                    value = self.bacnet.read(
                        f"{device_address} {sensor['object']} presentValue"
                    )

                    readings.append({
                        'timestamp': timestamp,
                        'sensor_name': sensor['name'],
                        'value': float(value),
                        'unit': self.get_sensor_unit(sensor['name'])
                    })
                    logger.debug(f"Read {sensor['name']}: {value}")

                except Exception as e:
                    logger.error(f"Error reading {sensor['name']}: {e}")

            return readings

        except Exception as e:
            logger.error(f"Error in read_sensors: {e}")
            return []

    def get_sensor_unit(self, sensor_name):
        """Return unit for sensor (customize based on your sensors)"""
        units = {
            'pool_temperature': '°C',
            'pool_ph': 'pH',
            'chlorine_level': 'ppm',
            'water_pressure': 'bar',
            'flow_rate': 'm³/h'
        }
        return units.get(sensor_name, '')

    def store_readings(self, readings):
        """Store readings in local database"""
        cursor = self.db_conn.cursor()

        for reading in readings:
            cursor.execute('''
                           INSERT INTO sensor_readings (timestamp, sensor_name, value, unit)
                           VALUES (?, ?, ?, ?)
                           ''', (
                               reading['timestamp'],
                               reading['sensor_name'],
                               reading['value'],
                               reading['unit']
                           ))

        self.db_conn.commit()
        logger.info(f"Stored {len(readings)} readings locally")

    def post_to_api(self):
        """Post unposted readings to Laravel API"""
        cursor = self.db_conn.cursor()

        # Get unposted readings
        cursor.execute('''
                       SELECT id, timestamp, sensor_name, value, unit
                       FROM sensor_readings
                       WHERE posted = 0
                       ORDER BY timestamp
                       ''')

        rows = cursor.fetchall()
        if not rows:
            logger.info("No new readings to post")
            return

        # Format data for API
        readings = [{
            'timestamp': row[1],
            'sensor_name': row[2],
            'value': row[3],
            'unit': row[4]
        } for row in rows]

        payload = {
            'device_id': 'raspberry-pi-001',  # Unique Pi identifier
            'readings': readings
        }

        try:
            # Post to Laravel API
            headers = {
                'Authorization': f"Bearer {CONFIG['api_token']}",
                'Content-Type': 'application/json'
            }

            response = requests.post(
                CONFIG['api_url'],
                json=payload,
                headers=headers,
                timeout=30
            )

            if response.status_code == 200:
                # Mark readings as posted
                reading_ids = [row[0] for row in rows]
                placeholders = ','.join('?' * len(reading_ids))
                cursor.execute(
                    f'UPDATE sensor_readings SET posted = 1 WHERE id IN ({placeholders})',
                    reading_ids
                )
                self.db_conn.commit()

                logger.info(f"Successfully posted {len(readings)} readings to API")

                # Clean up old posted data (keep last 7 days)
                cursor.execute('''
                               DELETE
                               FROM sensor_readings
                               WHERE posted = 1
                                 AND timestamp
                                   < datetime('now'
                                   , '-7 days')
                               ''')
                self.db_conn.commit()

            else:
                logger.error(f"API returned status {response.status_code}: {response.text}")

        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to post to API: {e}")

    def run(self):
        """Main service loop"""
        if not self.connect_bacnet():
            logger.error("Cannot start: BACnet connection failed")
            return

        logger.info("Reader service started")
        last_post_time = 0

        try:
            while True:
                # Read sensors
                readings = self.read_sensors()

                if readings:
                    self.store_readings(readings)

                # Post to API at configured interval
                if time.time() - last_post_time >= CONFIG['post_interval']:
                    self.post_to_api()
                    last_post_time = time.time()

                # Wait before next reading
                time.sleep(CONFIG['read_interval'])

        except KeyboardInterrupt:
            logger.info("Service stopped by user")
        finally:
            if self.bacnet:
                self.bacnet.disconnect()
            if self.db_conn:
                self.db_conn.close()


if __name__ == "__main__":
    reader = SensorReader()
    reader.run()
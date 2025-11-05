#!/usr/bin/env python3
"""
BACnet Device Simulator using BAC0
Creates a simulated BACnet device with analog and binary values
Compatible with BAC0 2025.9.15 and Python 3.13
Dynamically creates objects based on config.py
"""

import asyncio
import sys
from pathlib import Path
import BAC0
from BAC0.core.devices.local.factory import (
    analog_value,
    analog_input,
    binary_value,
)

# Add project root to path to import config
PROJECT_ROOT = Path(__file__).parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.config import Config


async def main():
    print("Starting BACnet Device Simulator...")

    # OPTION 1: Auto-detect IP (default)
    bacnet = BAC0.start(deviceId=Config.TARGET_DEVICE_ID)

    # OPTION 2: Specify IP explicitly (use this if running on separate machine)
    # bacnet = BAC0.start(ip='192.168.1.XXX/24', deviceId=Config.TARGET_DEVICE_ID)
    # Replace XXX with this machine's IP address

    # Wait a moment for initialization
    await asyncio.sleep(1)

    print(f"BACnet device started")
    print(f"Device ID: {Config.TARGET_DEVICE_ID}")
    print(f"IP Address: {bacnet.localIPAddr}")

    # Create local objects dynamically from config
    print("\nCreating BACnet objects from config...")

    sensors_config = Config.get_sensor_config()
    created_objects = []

    for sensor in sensors_config:
        try:
            # Parse object type and instance
            obj_type, obj_instance = sensor['object'].split(':')
            obj_instance = int(obj_instance)

            # Determine initial value based on unit
            if 'celsius' in sensor['unit'].lower() or 'temperature' in sensor['name'].lower():
                initial_value = 22.5
            elif 'percent' in sensor['unit'].lower() or 'humidity' in sensor['name'].lower():
                initial_value = 45.0
            elif 'pascal' in sensor['unit'].lower() or 'pressure' in sensor['name'].lower():
                initial_value = 101.3
            elif 'status' in sensor['unit'].lower():
                initial_value = 1  # Active
            else:
                initial_value = 0.0

            # Create the appropriate object type
            if obj_type == 'analogValue':
                obj = analog_value(
                    instance=obj_instance,
                    name=sensor['name'],
                    description=sensor['description'],
                    presentValue=initial_value,
                    properties={"units": sensor['unit']},
                    is_commandable=True
                )
            elif obj_type == 'analogInput':
                obj = analog_input(
                    instance=obj_instance,
                    name=sensor['name'],
                    description=sensor['description'],
                    presentValue=initial_value,
                    properties={"units": sensor['unit']}
                )
            elif obj_type == 'binaryValue':
                obj = binary_value(
                    instance=obj_instance,
                    name=sensor['name'],
                    description=sensor['description'],
                    presentValue=int(initial_value),
                    is_commandable=True
                )
            else:
                print(f"  ⚠ Unsupported object type: {obj_type} for {sensor['name']}")
                continue

            # Add object to the BACnet application
            obj.add_objects_to_application(bacnet)
            created_objects.append({
                'name': sensor['name'],
                'object': obj,
                'type': obj_type,
                'instance': obj_instance,
                'unit': sensor['unit']
            })

            print(f"  ✓ {sensor['name']} ({obj_type}:{obj_instance}) - {initial_value} {sensor['unit']}")

        except Exception as e:
            print(f"  ✗ Failed to create {sensor['name']}: {e}")

    print(f"\n✓ Created {len(created_objects)}/{len(sensors_config)} objects successfully!")

    print("\n" + "=" * 60)
    print("Device is now running and discoverable on the network")
    print(f"Device ID: {Config.TARGET_DEVICE_ID}")
    print("Press Ctrl+C to stop")
    print("=" * 60 + "\n")

    # Simulate changing values periodically
    counter = 0
    try:
        while True:
            await asyncio.sleep(5)
            counter += 1

            print(f"[Update {counter}]", end=" ")

            # Update each object based on its type
            for obj_info in created_objects:
                try:
                    obj_local = bacnet.local_objects[obj_info['name']]

                    # Generate new value based on sensor type
                    if 'temperature' in obj_info['name'].lower():
                        new_value = 22.5 + (counter % 10) * 0.5
                    elif 'humidity' in obj_info['name'].lower():
                        new_value = 45.0 + (counter % 8) * 2.0
                    elif 'pressure' in obj_info['name'].lower():
                        new_value = 101.3 + (counter % 5) * 0.2
                    elif 'status' in obj_info['name'].lower():
                        new_value = 1 if (counter % 10) < 5 else 0
                    else:
                        # Generic oscillation for unknown sensors
                        new_value = 50.0 + (counter % 20) * 2.5

                    # Update the value
                    obj_local.presentValue = new_value

                    # Format output based on type
                    if obj_info['type'] == 'binaryValue':
                        display_value = "Active" if new_value else "Inactive"
                    else:
                        display_value = f"{new_value:.1f} {obj_info['unit']}"

                    print(f"{obj_info['name']}: {display_value}", end=" | ")

                except Exception as e:
                    print(f"Error updating {obj_info['name']}: {e}", end=" | ")

            print()  # New line after all updates

    except KeyboardInterrupt:
        print("\n\nShutting down BACnet device...")
        await bacnet._disconnect()
        print("Device stopped.")


if __name__ == "__main__":
    asyncio.run(main())
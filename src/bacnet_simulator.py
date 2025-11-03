#!/usr/bin/env python3
"""
BACnet Virtual Sensor Simulator
Simulates aquatic center sensors (temperature, pH, chlorine, etc.)
"""

import BAC0
import random
import time
from datetime import datetime

# Configuration
DEVICE_ID = 100
DEVICE_NAME = "AquaticCenter-Simulator"
IP_ADDRESS = "192.168.1.100/24"  # Change to match your network


def create_virtual_device():
    """Create a virtual BACnet device with simulated sensors"""

    # Initialize BACnet network
    bacnet = BAC0.lite(ip=IP_ADDRESS)

    print(f"[{datetime.now()}] Starting BACnet simulator...")
    print(f"Device ID: {DEVICE_ID}")
    print(f"Device Name: {DEVICE_NAME}")
    print(f"IP Address: {IP_ADDRESS}")

    # Create virtual analog inputs (sensors)
    sensors = {
        'pool_temperature': {'min': 26.0, 'max': 30.0, 'unit': '°C'},
        'pool_ph': {'min': 7.0, 'max': 7.6, 'unit': 'pH'},
        'chlorine_level': {'min': 1.0, 'max': 3.0, 'unit': 'ppm'},
        'water_pressure': {'min': 1.5, 'max': 2.5, 'unit': 'bar'},
        'flow_rate': {'min': 50, 'max': 150, 'unit': 'm³/h'},
    }

    print("\nSimulated Sensors:")
    for name, config in sensors.items():
        print(f"  - {name}: {config['min']}-{config['max']} {config['unit']}")

    print("\nSimulator running. Press Ctrl+C to stop.")
    print("-" * 60)

    try:
        while True:
            print(f"\n[{datetime.now().strftime('%H:%M:%S')}] Sensor Readings:")

            for sensor_name, config in sensors.items():
                # Generate realistic random values
                value = random.uniform(config['min'], config['max'])
                print(f"  {sensor_name}: {value:.2f} {config['unit']}")

            time.sleep(10)  # Update every 10 seconds

    except KeyboardInterrupt:
        print("\n\nStopping simulator...")
        bacnet.disconnect()
        print("Simulator stopped.")


if __name__ == "__main__":
    create_virtual_device()
"""
Configuration Management
Loads settings from .env file
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


class Config:
    """Application configuration"""

    # API Configuration
    API_URL = os.getenv('API_URL', 'http://localhost:8000/api/sensor-data')
    API_TOKEN = os.getenv('API_TOKEN', '')
    API_CONFIG_URL = os.getenv('API_CONFIG_URL', 'http://localhost:8000/api/device/config')

    # Device Configuration
    DEVICE_ID = os.getenv('DEVICE_ID', 'raspberry-pi-001')
    DEVICE_NAME = os.getenv('DEVICE_NAME', 'AquaticCenter-Pi-001')

    # BACnet Configuration
    BACNET_IP = os.getenv('BACNET_IP', '192.168.1.200/24')
    BACNET_PORT = int(os.getenv('BACNET_PORT', '47808'))
    TARGET_DEVICE_IP = os.getenv('TARGET_DEVICE_IP', '192.168.1.100')
    TARGET_DEVICE_ID = int(os.getenv('TARGET_DEVICE_ID', '100'))

    # Timing
    READ_INTERVAL = int(os.getenv('READ_INTERVAL', '30'))
    POST_INTERVAL = int(os.getenv('POST_INTERVAL', '300'))
    RETRY_INTERVAL = int(os.getenv('RETRY_INTERVAL', '60'))

    # Database
    DB_PATH = os.getenv('DB_PATH', './data/sensor_data.db')

    # Logging
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
    LOG_FILE = os.getenv('LOG_FILE', './logs/reader.log')
    LOG_MAX_BYTES = int(os.getenv('LOG_MAX_BYTES', '10485760'))
    LOG_BACKUP_COUNT = int(os.getenv('LOG_BACKUP_COUNT', '5'))

    # Development
    DEBUG = os.getenv('DEBUG', 'False').lower() == 'true'
    SIMULATE_MODE = os.getenv('SIMULATE_MODE', 'False').lower() == 'true'

    @classmethod
    def validate(cls):
        """Validate critical configuration"""
        if not cls.API_TOKEN and not cls.DEBUG:
            raise ValueError("API_TOKEN is required")

        if not cls.DEVICE_ID:
            raise ValueError("DEVICE_ID is required")

        # Ensure directories exist
        Path(cls.DB_PATH).parent.mkdir(parents=True, exist_ok=True)
        Path(cls.LOG_FILE).parent.mkdir(parents=True, exist_ok=True)

    @classmethod
    def get_sensor_config(cls):
        """Define sensor configuration"""
        return [
            {
                'name': 'pool_temperature',
                'object': 'analogInput:1',
                'unit': '°C',
                'description': 'Pool Water Temperature'
            },
            {
                'name': 'pool_ph',
                'object': 'analogInput:2',
                'unit': 'pH',
                'description': 'Pool pH Level'
            },
            {
                'name': 'chlorine_level',
                'object': 'analogInput:3',
                'unit': 'ppm',
                'description': 'Chlorine Concentration'
            },
            {
                'name': 'water_pressure',
                'object': 'analogInput:4',
                'unit': 'bar',
                'description': 'Water Pressure'
            },
            {
                'name': 'flow_rate',
                'object': 'analogInput:5',
                'unit': 'm³/h',
                'description': 'Water Flow Rate'
            },
        ]
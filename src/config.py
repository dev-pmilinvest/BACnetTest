"""
Configuration Management
Loads settings from .env file
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Get the project root directory (parent of src/)
if __name__ == '__main__':
    PROJECT_ROOT = Path(__file__).parent.parent
else:
    # When imported, find project root
    PROJECT_ROOT = Path(__file__).parent.parent

# Change to project root to ensure relative paths work
os.chdir(PROJECT_ROOT)

# Load environment variables from project root
load_dotenv(PROJECT_ROOT / '.env')

class Config:
    """Application configuration"""

    # API Configuration
    API_URL = os.getenv('API_URL', 'http://localhost:8000/api')
    API_TOKEN = os.getenv('API_TOKEN', '')

    # Device Configuration
    DEVICE_NAME = os.getenv('DEVICE_NAME', 'AquaticCenter-Pi-001')

    # BACnet Configuration - Reader
    BACNET_IP = os.getenv('BACNET_IP', '192.168.1.116/24')
    BACNET_PORT = int(os.getenv('BACNET_PORT', '47809'))  # Different port to avoid conflict

    # BACnet Configuration - Target Device (Simulator)
    TARGET_DEVICE_IP = os.getenv('TARGET_DEVICE_IP', '192.168.1.116')
    TARGET_DEVICE_ID = int(os.getenv('TARGET_DEVICE_ID', '100'))
    BACNET_TARGET_PORT = int(os.getenv('BACNET_TARGET_PORT', '47808'))  # Simulator's port

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

        # Ensure directories exist
        Path(cls.DB_PATH).parent.mkdir(parents=True, exist_ok=True)
        Path(cls.LOG_FILE).parent.mkdir(parents=True, exist_ok=True)

    @classmethod
    def get_sensor_config(cls):
        """
        Define sensor configuration
        Maps to the objects created in the BACnet simulator
        """
        return [
            {
                'name': 'Temperature',
                'object': 'analogValue:1',
                'unit': 'degreesCelsius',
                'description': 'Room Temperature'
            },
            {
                'name': 'Humidity',
                'object': 'analogValue:2',
                'unit': 'percent',
                'description': 'Room Humidity'
            },
            {
                'name': 'Pressure',
                'object': 'analogInput:3',
                'unit': 'kilopascals',
                'description': 'Air Pressure'
            },
            {
                'name': 'SystemStatus',
                'object': 'binaryValue:1',
                'unit': 'status',
                'description': 'System On/Off Status'
            },
        ]
"""
API Client for Laravel Backend
Handles all HTTP communication with the Laravel API
"""

import requests
from typing import Dict, List, Optional
from src.config import Config
from src.logger import setup_logger

logger = setup_logger(__name__)


class APIClient:
    """Client for communicating with Laravel API"""

    def __init__(self):
        self.api_url = Config.API_URL
        self.config_url = Config.API_CONFIG_URL
        self.device_id = Config.DEVICE_NAME
        self.session = requests.Session()
        self.session.headers.update({
            'Authorization': f'Bearer {Config.API_TOKEN}',
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        })

    def post_sensor_data(self, readings: List[Dict]) -> bool:
        """
        Post sensor readings to Laravel API

        Args:
            readings: List of sensor reading dictionaries

        Returns:
            True if successful, False otherwise
        """
        if not readings:
            logger.warning("No readings to post")
            return False

        payload = {
            'device_id': self.device_id,
            'readings': readings
        }

        try:
            logger.info(f"Posting {len(readings)} readings to API...")

            response = self.session.post(
                self.api_url,
                json=payload,
                timeout=30
            )

            if response.status_code == 200:
                data = response.json()
                logger.info(f"✓ Successfully posted {data.get('stored_count', len(readings))} readings")
                return True
            else:
                logger.error(f"API returned status {response.status_code}: {response.text}")
                return False

        except requests.exceptions.ConnectionError:
            logger.error("Connection failed: Could not reach API server")
            return False
        except requests.exceptions.Timeout:
            logger.error("Request timeout: API server not responding")
            return False
        except requests.exceptions.RequestException as e:
            logger.error(f"Request failed: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error: {e}", exc_info=True)
            return False

    def get_device_config(self) -> Optional[Dict]:
        """
        Get device configuration from API

        Returns:
            Configuration dictionary or None if failed
        """
        try:
            logger.debug("Fetching device configuration...")

            response = self.session.post(
                self.config_url,
                json={'device_id': self.device_id},
                timeout=10
            )

            if response.status_code == 200:
                data = response.json()
                logger.info("✓ Configuration fetched successfully")
                return data.get('config', {})
            else:
                logger.warning(f"Could not fetch config: {response.status_code}")
                return None

        except Exception as e:
            logger.warning(f"Failed to fetch config: {e}")
            return None

    def health_check(self) -> bool:
        """
        Check if API is accessible

        Returns:
            True if API is healthy, False otherwise
        """
        try:
            health_url = Config.API_URL.replace('/sensor-data', '/health')
            response = self.session.get(health_url, timeout=5)
            return response.status_code == 200
        except:
            return False

    def close(self):
        """Close the session"""
        self.session.close()
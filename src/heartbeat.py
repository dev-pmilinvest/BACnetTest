import time
import requests
from src.config import Config

while True:
    try:
        heartbeat_url = Config.API_URL.replace('/sensor-data', '/heartbeat')
        requests.post(
            heartbeat_url,
            json={'device_id': Config.DEVICE_ID, 'status': 'alive'},
            timeout=10
        )
    except:
        pass
    time.sleep(300)  # Every 5 minutes
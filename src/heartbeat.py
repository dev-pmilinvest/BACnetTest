import time
import requests
from src.config import Config

while True:
    try:
        requests.post(
            Config.API_URL + "/heartbeat",
            json={'device_id': Config.DEVICE_NAME, 'status': 'alive'},
            timeout=10
        )
    except:
        pass
    time.sleep(300)  # Every 5 minutes
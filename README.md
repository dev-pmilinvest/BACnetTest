# Heitz - Raspberry Pi BACnet Test

BACnet sensor data collection service

## Requirements

- Python 3.13+ (tested with 3.13.5, **won't work with Python 3.12-**)
- Raspberry Pi 5 (or any system for development)
- Laravel API backend (already setup)
- Network access to BACnet devices (optional *— not tested*)

## 1.Install Locally

### 1.1. Clone repository (public)

```bash
git clone https://github.com/dev-pmilinvest/BACnetTest.git
```

### 1.2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 1.3. Configure Environment

Copy `.env.example` to `.env` and fill in your values:

```bash
# todo change 'whatever-you-want' to an identifier unique to you (e.g.: dev4)
DEVICE_ID=raspberry-pi-test-whatever-you-want
DEVICE_NAME=Raspberry-Pi-Test-whatever-you-want

# todo set BACNET_IP to <your IPv4>/24
BACNET_IP=192.168.1.200/24

# todo set TARGET_DEVICE_IP to <your IPv4>
TARGET_DEVICE_IP=192.168.1.200
```

### 1.4. Verify Setup

```bash
python test_setup.py
```

Should show all ✓ checks passing.

## 2. Running the Service

### 2.1. Development Mode (Simulated Data)

1. Make sure `SIMULATE_MODE=True` in `.env`
2. Run `python -m src.sensor_reader`

You should see:
```
Heitz - Sensor Reader Service
Device ID: <what you put in .env>
...
✓ Service started successfully
```

### 2.2. With BACnet Simulator

**Terminal 1** (Simulator):
```bash
python -m src.bacnet_simulator
```

**Terminal 2** (Reader):
1. Set `SIMULATE_MODE=False` in `.env`
2. Update `BACNET_IP` to match your network in `.env`
3. Run `python -m src.sensor_reader`

### 2.3. Production Mode (Real Device — *not tested*)

1. Set `SIMULATE_MODE=False` in `.env`
2. Configure correct BACnet IPs in `.env`
3. Run: `python -m src.sensor_reader`

### 2.4. Check the results at [hiecoconso-nicolas.pmil.dev/bacnet-test](https://hiecoconso-nicolas.pmil.dev/bacnet-test)

## 3. Raspberry Installation

### 3.1. SD card Image

1. Plug your microSD card in your computer
2. Download and run [Raspberry Pi Imager](https://www.raspberrypi.com/software/)
3. From the main menu \
3.1. Select Raspberry Pi 5 as ***model*** \
3.2. Select Raspberry Pi OS (64-bit) as ***OS*** \
3.3. Select your plugged microSD card as ***storage*** \
3.4. Click next
4. **Don't click yes yet**, select Edit Settings
5. Under the *General* tab \
5.1. Check ***Set hostname*** & choose your hostname or leave default *(e.g.: raspberrypi.local)* \
5.2. Check ***Set username and password*** & choose your username and password *(e.g.: pi, raspberry)* \
5.3. Check ***Configure wireless LAN*** & fill-in your Wi-Fi SSID and password \
5.4. Select your Wi-Fi Country *(e.g.: FR)* \
5.5. Check ***Set locale settings*** & set your timezone *(e.g.: FR)*
6. Under the *Services* tab \
6.1. Check ***Enable SSH*** & select ***Allow public-key authentication only*** \
6.2. Add an ssh public key (choose one already on your computer or create a new pair, doesn't matter)
7. Click Save
8. Back in the main menu, click Yes
9. Click Yes on the popup that appears
10. Once the imager finishes, remove the microSD card from your computer

### 3.2. MobaXterm SSH Connection Setup

1. Plug the microSD in the Raspberry
2. Power the Raspberry on and wait a minute *(it takes ~60-90 seconds for the image to boot)*
3. from a terminal, ping the Raspberry until it responds \
`ping <hostname set in general settings>` *(e.g.: `ping raspberrypi.local`)*
4. Once you get a response, the Raspberry is ready to connect
5. Open MobaXterm and create a new SSH session \
5.1. **Remote host**: \<hostname set in general settings\> *(e.g.: raspberrypi.local)* \
5.2. Check **Specify Username**: \<username set in general settings\> *(e.g.: pi)*\
5.3. **Port**: 22
6. Open the session to verify

### 3.3. Raspberry Pi Configuration

From your MobaXterm session terminal :

1. Install global dependencies \
`sudo apt update` \
`sudo apt install git -y`
2. Create projects directory \
`mkdir -p ~/projects` \
`cd ~/projects`
3. Clone repository (public) \
`git clone https://github.com/dev-pmilinvest/BACnetTest.git` \
`cd BACnetTest/`
4. Install project dependencies \
`sudo apt install python3-venv -y` \
`python3 -m venv venv` \
`source venv/bin/activate` \
`pip install --upgrade pip` \
`pip install -r requirements.txt`
5. Configure Environment \
Copy `.env.example` to `.env` and fill in your values:
    ```bash
    # todo change 'whatever-you-want' to an identifier unique to you (e.g.: dev4)
    DEVICE_ID=raspberry-pi-test-whatever-you-want
    DEVICE_NAME=Raspberry-Pi-Test-whatever-you-want
    
    # todo set BACNET_IP to <your IPv4>/24
    BACNET_IP=192.168.1.200/24
    
    # todo set TARGET_DEVICE_IP to <your IPv4>
    TARGET_DEVICE_IP=192.168.1.200
    ```
### 3.4. Running the Service

You can refer to [2. Running the Service](#2-running-the-service), it's the same setup

## 4. Upcoming

Connect to a remote BACnet simulator


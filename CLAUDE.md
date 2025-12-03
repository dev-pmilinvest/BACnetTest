# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a Raspberry Pi-based BACnet sensor reading system that collects building automation data and syncs it with a Laravel backend API. The system is designed to run on Raspberry Pi 5 with Python 3.13+ and supports both real BACnet devices and simulation mode for development.

## Key Commands

### Setup
```bash
# Install dependencies
pip install -r requirements.txt

# Verify setup
python test_setup.py

# Configure environment
cp .env.example .env
# Edit .env with your DEVICE_NAME, BACNET_IP, TARGET_DEVICE_IP
```

### Running Services

**Development Mode (simulated data):**
```bash
# Set SIMULATE_MODE=True in .env
python -m src.sensor_reader
```

**With BACnet Simulator:**
```bash
# Terminal 1: Start simulator
python -m src.bacnet_simulator

# Terminal 2: Start reader (SIMULATE_MODE=False in .env)
python -m src.sensor_reader
```

**Other Services:**
```bash
python -m src.heartbeat       # Sends heartbeat every 5 minutes
python -m src.update_checker  # Checks for updates every 5 minutes
```

### Testing
```bash
pytest                        # Run all tests
pytest tests/test_specific.py # Run specific test file
```

## Architecture

### Service Components

**`src/sensor_reader.py`** - Main service that orchestrates everything:
- Connects to BACnet network using BAC0 library
- Reads sensor values from configured BACnet points (or simulates them)
- Stores readings in local SQLite database
- Periodically syncs unposted readings to Laravel API
- Uses asyncio for async BACnet operations with BAC0 2025.9.15+

**`src/bacnet_simulator.py`** - BACnet device simulator:
- Creates a simulated BACnet device for development/testing
- Dynamically creates BACnet objects based on `Config.get_sensor_config()`
- Updates sensor values periodically to simulate changing readings
- Runs on same machine but uses different port than reader

**`src/database.py`** - SQLite database manager:
- Stores sensor readings locally with `posted` flag
- Retrieves unposted readings for API sync
- Marks readings as posted after successful API sync
- Cleans up old posted data (default: keep 7 days)

**`src/api_client.py`** - Laravel API client:
- Handles all HTTP communication with backend
- Posts sensor data in batches
- Checks for updates (git commit-based versioning)
- Includes health checks and heartbeat endpoints

**`src/config.py`** - Configuration management:
- Loads settings from `.env` file
- Defines sensor configuration via `Config.get_sensor_config()`
- Auto-creates required directories (`data/`, `logs/`)

**`src/heartbeat.py`** - Simple heartbeat service:
- Sends "alive" signals to API every 5 minutes
- Runs in background to monitor device connectivity

**`src/update_checker.py`** - Auto-update service:
- Checks API for updates every 5 minutes
- Performs git pull and restarts services on update
- Includes rollback capability on failure

### Configuration Pattern

**All BACnet sensors are defined in one place:** `src/config.py::Config.get_sensor_config()`

This method returns a list of sensor configurations used by both:
1. `bacnet_simulator.py` - Creates matching BACnet objects
2. `sensor_reader.py` - Knows which points to read

Each sensor config has:
- `name`: Sensor identifier
- `object`: BACnet object type and instance (e.g., "analogValue:1")
- `unit`: Engineering unit (e.g., "degreesCelsius")
- `description`: Human-readable description

### Data Flow

1. **Reading cycle** (every `READ_INTERVAL` seconds):
   - `SensorReader.read_sensors()` reads all configured BACnet points
   - Readings stored locally via `Database.store_readings()`

2. **Sync cycle** (every `POST_INTERVAL` seconds):
   - `SensorReader.sync_with_api()` gets unposted readings
   - Posts to Laravel API via `APIClient.post_sensor_data()`
   - Marks readings as posted on success
   - Cleans up old posted data

3. **BACnet Communication**:
   - Reader connects to BACnet network via BAC0 library
   - Tries device object read first (if connected)
   - Falls back to direct read using device address + object identifier
   - All BAC0 async operations use `await` (2025.x compatibility)

### Python 3.13 & BAC0 Compatibility

This codebase requires Python 3.13+ and BAC0 2025.9.15:
- **BAC0.start()** is synchronous (no await)
- **BAC0.device()** is async (requires await)
- **point.value** access is async (requires await)
- All BACnet operations run within asyncio event loop

### Environment Variables

Critical settings in `.env`:
- `DEVICE_NAME`: Unique identifier for this Raspberry Pi
- `BACNET_IP`: Reader's network interface (format: "192.168.1.x/24")
- `TARGET_DEVICE_IP`: Target BACnet device IP
- `TARGET_DEVICE_ID`: Target BACnet device ID (default: 100)
- `SIMULATE_MODE`: Set to `True` for development without BACnet hardware
- `API_URL`: Laravel backend URL
- `API_TOKEN`: Bearer token for API authentication

## Important Notes

- **Simulate mode is for development**: Set `SIMULATE_MODE=True` to test without BACnet hardware
- **Port conflicts**: Reader uses 47809, simulator uses 47808 (avoid conflicts)
- **Network requirement**: For real BACnet, reader and device must be on same subnet
- **Graceful shutdown**: All services handle SIGINT/SIGTERM for clean exits
- **Local-first storage**: Readings stored locally first, synced to API later (network resilience)
- **Update mechanism**: Uses git commit hashes as versions for rolling updates
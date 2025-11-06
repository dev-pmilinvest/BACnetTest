#!/usr/bin/env python3
"""
Setup verification script
Tests that all dependencies are properly installed
"""

import sys
print(f"Python version: {sys.version}")
print()

# Test imports
print("Testing imports...")
tests = []

try:
    import BAC0
    # version = BAC0.__version__
    version = getattr(BAC0, "__version__", "unknown")
    print(f"✓ BAC0 {version}")
    # if version.startswith('2025'):
    #     print(f"  ℹ Using BAC0 {version} (Python 3.13 compatible)")
    tests.append(True)
except ImportError as e:
    print(f"✗ BAC0 not found: {e}")
    tests.append(False)

try:
    import requests
    print(f"✓ requests {requests.__version__}")
    tests.append(True)
except ImportError as e:
    print(f"✗ requests not found: {e}")
    tests.append(False)

try:
    import dotenv
    print(f"✓ python-dotenv")
    tests.append(True)
except ImportError as e:
    print(f"✗ python-dotenv not found: {e}")
    tests.append(False)

try:
    import colorlog
    print(f"✓ colorlog")
    tests.append(True)
except ImportError as e:
    print(f"✗ colorlog not found: {e}")
    tests.append(False)

try:
    import sqlite3
    print(f"✓ sqlite3 (built-in)")
    tests.append(True)
except ImportError as e:
    print(f"✗ sqlite3 not found: {e}")
    tests.append(False)

print()

# Test asyncio (should be built-in for Python 3.13)
try:
    import asyncio
    print(f"✓ asyncio available (Python {sys.version_info.major}.{sys.version_info.minor})")
    tests.append(True)
except ImportError:
    print(f"✗ asyncio not available")
    tests.append(False)

print()

# Test project structure
print("Checking project structure...")
import os
from pathlib import Path

required_dirs = ['logs', 'data', 'src']
for dir_name in required_dirs:
    if Path(dir_name).exists():
        print(f"✓ {dir_name}/ directory exists")
        tests.append(True)
    else:
        print(f"✗ {dir_name}/ directory missing")
        tests.append(False)

required_files = ['.env', 'requirements.txt', 'src/__init__.py', 'src/config.py']
for file_name in required_files:
    if Path(file_name).exists():
        print(f"✓ {file_name} exists")
        tests.append(True)
    else:
        print(f"✗ {file_name} missing")
        tests.append(False)

print()

# Test configuration loading
try:
    from src.config import Config
    Config.validate()
    print(f"✓ Configuration loaded successfully")
    print(f"  - Device Name: {Config.DEVICE_NAME}")
    print(f"  - API URL: {Config.API_URL}")
    print(f"  - Simulate Mode: {Config.SIMULATE_MODE}")
    tests.append(True)
except Exception as e:
    print(f"✗ Configuration error: {e}")
    tests.append(False)

print()

# Summary
passed = sum(tests)
total = len(tests)
print("=" * 60)
print(f"Tests passed: {passed}/{total}")

if passed == total:
    print("✓ All checks passed! You're ready to go.")
    print()
    print("Next steps:")
    print("1. Update .env with your actual values")
    print("2. Run: python src/sensor_reader.py")
else:
    print("✗ Some checks failed. Please fix the issues above.")
    sys.exit(1)
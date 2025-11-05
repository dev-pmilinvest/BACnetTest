"""
Logging Configuration
Provides colorized console and file logging with UTF-8 support
"""

import logging
import sys
import io
from logging.handlers import RotatingFileHandler
from pathlib import Path
import colorlog
from src.config import Config

def setup_logger(name: str = __name__):
    """
    Set up logger with console and file handlers

    Args:
        name: Logger name

    Returns:
        Configured logger instance
    """
    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, Config.LOG_LEVEL))

    # Prevent duplicate handlers
    if logger.handlers:
        return logger

    # Console Handler with colors and UTF-8 support
    # Force UTF-8 encoding on Windows
    if sys.platform == 'win32':
        # Reconfigure stdout to use UTF-8
        sys.stdout.reconfigure(encoding='utf-8')
        console_stream = sys.stdout
    else:
        console_stream = sys.stdout

    console_handler = colorlog.StreamHandler(console_stream)
    console_handler.setLevel(logging.DEBUG if Config.DEBUG else logging.INFO)

    # Set UTF-8 encoding for the handler
    console_handler.setStream(console_stream)

    console_formatter = colorlog.ColoredFormatter(
        '%(log_color)s%(asctime)s - %(name)s - %(levelname)s - %(message)s%(reset)s',
        datefmt='%Y-%m-%d %H:%M:%S',
        log_colors={
            'DEBUG': 'cyan',
            'INFO': 'green',
            'WARNING': 'yellow',
            'ERROR': 'red',
            'CRITICAL': 'red,bg_white',
        }
    )
    console_handler.setFormatter(console_formatter)
    logger.addHandler(console_handler)

    # File Handler with rotation and UTF-8 encoding
    Path(Config.LOG_FILE).parent.mkdir(parents=True, exist_ok=True)

    file_handler = RotatingFileHandler(
        Config.LOG_FILE,
        maxBytes=Config.LOG_MAX_BYTES,
        backupCount=Config.LOG_BACKUP_COUNT,
        encoding='utf-8'  # Force UTF-8 for file
    )
    file_handler.setLevel(logging.DEBUG)

    file_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    file_handler.setFormatter(file_formatter)
    logger.addHandler(file_handler)

    return logger
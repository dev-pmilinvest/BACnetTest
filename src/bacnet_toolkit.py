"""
BACnet Toolkit
Read, write, and release values on BACnet devices
Compatible with BAC0 2025.9.15 and Python 3.13
"""

import asyncio
import argparse
import sys
from typing import Optional

try:
    import BAC0
    BAC0_AVAILABLE = True
except ImportError:
    BAC0_AVAILABLE = False
    print("Error: BAC0 not installed. Run: pip install BAC0")
    sys.exit(1)

from src.config import Config
from src.logger import setup_logger

logger = setup_logger(__name__)


class BACnetWriter:
    """Service for writing values to BACnet devices"""

    def __init__(self):
        self.bacnet = None

    async def connect(self) -> bool:
        """
        Connect to BACnet network

        Returns:
            True if successful
        """
        try:
            logger.info(f"Connecting to BACnet network: {Config.BACNET_IP}:{Config.BACNET_PORT}")

            # BAC0 2025.x - use start() without await
            self.bacnet = BAC0.start(ip=Config.BACNET_IP, port=Config.BACNET_PORT)

            logger.info("Connected to BACnet network")

            # Wait for network to stabilize
            await asyncio.sleep(2)
            return True

        except Exception as e:
            logger.error(f"Failed to connect to BACnet: {e}", exc_info=True)
            return False

    async def write_value(
        self,
        object_type: str,
        object_instance: int,
        value: float,
        priority: int = 16,
        device_ip: Optional[str] = None,
        device_port: Optional[int] = None
    ) -> bool:
        """
        Write a value to a BACnet object

        Args:
            object_type: BACnet object type (e.g., 'analog-value', 'binary-value')
            object_instance: Object instance number
            value: Value to write
            priority: BACnet priority (1-16, default 16)
            device_ip: Target device IP (uses config default if not provided)
            device_port: Target device port (uses config default if not provided)

        Returns:
            True if successful
        """
        if not self.bacnet:
            logger.error("BACnet not connected")
            return False

        # Use config defaults if not provided
        target_ip = device_ip or Config.TARGET_DEVICE_IP
        target_port = device_port or Config.BACNET_TARGET_PORT
        target_address = f"{target_ip}:{target_port}"

        try:
            # Construct the write request
            # Format: "address objectType instance presentValue value - priority"
            write_point = f"{target_address} {object_type} {object_instance} presentValue {value} - {priority}"

            logger.info(f"Writing: {object_type}:{object_instance} = {value} @ priority {priority}")
            logger.debug(f"Write request: {write_point}")

            # BAC0 2025.x - write() may be sync or async depending on version
            result = self.bacnet.write(write_point)
            if asyncio.iscoroutine(result):
                await result

            logger.info(f"Successfully wrote {value} to {object_type}:{object_instance}")
            return True

        except Exception as e:
            logger.error(f"Failed to write to {object_type}:{object_instance}: {e}", exc_info=True)
            return False

    async def release_value(
        self,
        object_type: str,
        object_instance: int,
        priority: int = 16,
        device_ip: Optional[str] = None,
        device_port: Optional[int] = None
    ) -> bool:
        """
        Release a priority in a BACnet object (write null)

        Args:
            object_type: BACnet object type
            object_instance: Object instance number
            priority: BACnet priority to release (1-16)
            device_ip: Target device IP
            device_port: Target device port

        Returns:
            True if successful
        """
        if not self.bacnet:
            logger.error("BACnet not connected")
            return False

        target_ip = device_ip or Config.TARGET_DEVICE_IP
        target_port = device_port or Config.BACNET_TARGET_PORT
        target_address = f"{target_ip}:{target_port}"

        try:
            # Write null to release the priority
            write_point = f"{target_address} {object_type} {object_instance} presentValue null - {priority}"

            logger.info(f"Releasing priority {priority} on {object_type}:{object_instance}")
            logger.debug(f"Release request: {write_point}")

            # BAC0 2025.x - write() may be sync or async depending on version
            result = self.bacnet.write(write_point)
            if asyncio.iscoroutine(result):
                await result

            logger.info(f"Successfully released priority {priority} on {object_type}:{object_instance}")
            return True

        except Exception as e:
            logger.error(f"Failed to release {object_type}:{object_instance}: {e}", exc_info=True)
            return False

    async def read_value(
        self,
        object_type: str,
        object_instance: int,
        device_ip: Optional[str] = None,
        device_port: Optional[int] = None
    ) -> Optional[float]:
        """
        Read the current value of a BACnet object

        Args:
            object_type: BACnet object type
            object_instance: Object instance number
            device_ip: Target device IP
            device_port: Target device port

        Returns:
            Current value or None if read failed
        """
        if not self.bacnet:
            logger.error("BACnet not connected")
            return None

        target_ip = device_ip or Config.TARGET_DEVICE_IP
        target_port = device_port or Config.BACNET_TARGET_PORT
        target_address = f"{target_ip}:{target_port}"

        try:
            read_point = f"{target_address} {object_type} {object_instance} presentValue"

            value = await self.bacnet.read(read_point)

            logger.info(f"Current value of {object_type}:{object_instance}: {value}")
            return float(value) if value is not None else None

        except Exception as e:
            logger.error(f"Failed to read {object_type}:{object_instance}: {e}", exc_info=True)
            return None

    async def disconnect(self):
        """Disconnect from BACnet network"""
        if self.bacnet:
            try:
                await self.bacnet._disconnect()
                logger.info("Disconnected from BACnet network")
            except Exception as e:
                logger.debug(f"Disconnect error (may be normal): {e}")


async def main_async(args):
    """Async main function"""
    writer = BACnetWriter()

    try:
        # Connect to BACnet
        if not await writer.connect():
            logger.error("Failed to connect to BACnet network")
            return 1

        # Parse object specification
        if ':' in args.object:
            obj_type, obj_instance = args.object.split(':')
            obj_instance = int(obj_instance)
        else:
            logger.error("Object must be in format 'type:instance' (e.g., 'analog-value:58317')")
            return 1

        # Execute the requested action
        if args.action == 'write':
            if args.value is None:
                logger.error("Value is required for write action")
                return 1

            # Read current value first
            current = await writer.read_value(obj_type, obj_instance, args.device_ip, args.device_port)
            if current is not None:
                logger.info(f"Current value: {current}")

            # Write new value
            success = await writer.write_value(
                obj_type, obj_instance, args.value, args.priority,
                args.device_ip, args.device_port
            )

            if success:
                # Verify the write
                await asyncio.sleep(0.5)
                new_value = await writer.read_value(obj_type, obj_instance, args.device_ip, args.device_port)
                if new_value is not None:
                    logger.info(f"Verified new value: {new_value}")

            return 0 if success else 1

        elif args.action == 'release':
            success = await writer.release_value(
                obj_type, obj_instance, args.priority,
                args.device_ip, args.device_port
            )
            return 0 if success else 1

        elif args.action == 'read':
            value = await writer.read_value(obj_type, obj_instance, args.device_ip, args.device_port)
            return 0 if value is not None else 1

    finally:
        await writer.disconnect()


def main():
    """Entry point with argument parsing"""
    parser = argparse.ArgumentParser(
        description='BACnet toolkit for reading, writing, and releasing values',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Write value 25.5 to analog-value:58317 at priority 8
  python -m src.bacnet_toolkit write analog-value:58317 25.5 --priority 8

  # Release priority 8 on analog-value:58317
  python -m src.bacnet_toolkit release analog-value:58317 --priority 8

  # Read current value
  python -m src.bacnet_toolkit read analog-value:58317

  # Write to a specific device
  python -m src.bacnet_toolkit write analog-value:58317 25.5 --device-ip 192.168.1.100 --device-port 47808
        """
    )

    parser.add_argument(
        'action',
        choices=['write', 'release', 'read'],
        help='Action to perform'
    )

    parser.add_argument(
        'object',
        help='BACnet object in format "type:instance" (e.g., analog-value:58317)'
    )

    parser.add_argument(
        'value',
        type=float,
        nargs='?',
        help='Value to write (required for write action)'
    )

    parser.add_argument(
        '--priority', '-p',
        type=int,
        default=16,
        choices=range(1, 17),
        metavar='1-16',
        help='BACnet priority (1-16, default: 16)'
    )

    parser.add_argument(
        '--device-ip',
        help=f'Target device IP (default: {Config.TARGET_DEVICE_IP})'
    )

    parser.add_argument(
        '--device-port',
        type=int,
        help=f'Target device port (default: {Config.BACNET_TARGET_PORT})'
    )

    args = parser.parse_args()

    # Validate write requires value
    if args.action == 'write' and args.value is None:
        parser.error("write action requires a value argument")

    # Run async main
    exit_code = asyncio.run(main_async(args))
    sys.exit(exit_code)


if __name__ == "__main__":
    main()

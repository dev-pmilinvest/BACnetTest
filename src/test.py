# src/test.py
import asyncio
import BAC0
from BAC0.core.devices.local.factory import analog_input, binary_value


async def run_device():
    dev = BAC0.lite()

    async with dev:
        print(f"[INFO] BAC0 device running: {dev}")

        analog_input(
            name="pool_temperature",
            description="Pool Water Temperature",
            properties={"units": "degreesCelsius"}  # valid BACnet unit
        )

        analog_input(
            name="pool_ph",
            description="Pool pH Level"
            # no units needed
        )

        analog_input(
            name="chlorine_level",
            description="Chlorine Level"
            # no units needed
        )

        analog_input(
            name="water_pressure",
            description="Water Pressure"
            # remove "bar" — BACnet does not recognize it
        )

        analog_input(
            name="flow_rate",
            description="Water Flow Rate"
            # leave units blank
        )

        binary_value(
            name="pump_status",
            description="Pump On/Off",
            presentValue=False
        )

        print("[INFO] Objects created. Simulator running for 300 seconds...")

        await asyncio.sleep(300)


if __name__ == "__main__":
    asyncio.run(run_device())

"""
Diagnostic script to explore BACnet device properties
"""
import asyncio
import BAC0

async def diagnose():
    # Connect to BACnet
    bacnet = BAC0.start(ip='192.168.1.18/24', port=47809)
    await asyncio.sleep(2)

    target = "192.168.1.43:47808"
    device_id = 128143

    print(f"\n{'='*60}")
    print(f"Diagnosing BACnet device at {target} (ID: {device_id})")
    print(f"{'='*60}\n")

    # Try to connect to device
    device = None
    try:
        device = await BAC0.device(target, device_id, bacnet)
        print(f"Connected to device: {device.properties.name}")
        print(f"\nFirst 5 analog-value points:")
        count = 0
        for point in device.points:
            if 'analog-value' in str(point.properties.type):
                print(f"  - {point.properties.name} ({point.properties.type}:{point.properties.address})")
                count += 1
                if count >= 5:
                    break
    except Exception as e:
        print(f"Could not create device object: {e}")

    # Test with CORRECT instance IDs from the device
    print(f"\n{'='*60}")
    print("Testing priority array reads with CORRECT instance IDs")
    print(f"{'='*60}\n")

    # These are the actual instance IDs from the device
    test_objects = [
        ('analog-value', 58317, 'Consigne Temp Reprise'),
        ('analog-value', 29619, 'Consigne Poids Eau'),
        ('analog-value', 59581, 'Consigne Temp Eau Bassin 2'),
    ]

    for obj_type, instance, name in test_objects:
        print(f"\n{name} ({obj_type}:{instance}):")

        # Read presentValue
        try:
            point = f"{target} {obj_type} {instance} presentValue"
            result = await bacnet.read(point)
            print(f"  presentValue: {result}")
        except Exception as e:
            print(f"  presentValue: ERROR - {e}")

        # Read priorityArray by name
        try:
            point = f"{target} {obj_type} {instance} priorityArray"
            result = await bacnet.read(point)
            print(f"  priorityArray (by name): {result}")
            if result and hasattr(result, 'dict_contents'):
                print(f"    dict_contents(): {result.dict_contents()}")
        except Exception as e:
            print(f"  priorityArray (by name): ERROR - {e}")

        # Read priorityArray by ID 87
        try:
            point = f"{target} {obj_type} {instance} 87"
            result = await bacnet.read(point)
            print(f"  priorityArray (by ID 87): {result}")
            if result and hasattr(result, 'dict_contents'):
                print(f"    dict_contents(): {result.dict_contents()}")
        except Exception as e:
            print(f"  priorityArray (by ID 87): ERROR - {e}")

        # Read propertyList to see what's available
        try:
            point = f"{target} {obj_type} {instance} propertyList"
            result = await bacnet.read(point)
            print(f"  propertyList: {result}")
        except Exception as e:
            print(f"  propertyList: ERROR - {e}")

    # Also test reading via device point object
    if device:
        print(f"\n{'='*60}")
        print("Testing via device point object")
        print(f"{'='*60}\n")

        try:
            point = device['Consigne Temp Reprise']
            print(f"Point: {point.properties.name}")
            print(f"  Type: {point.properties.type}")
            print(f"  Address: {point.properties.address}")

            # Try to get priority array via point
            if hasattr(point, 'priority_array'):
                pa = point.priority_array
                if asyncio.iscoroutine(pa):
                    pa = await pa
                print(f"  priority_array attr: {pa}")

            # Get bacnet properties
            if hasattr(point, 'bacnet_properties'):
                props = point.bacnet_properties
                if asyncio.iscoroutine(props):
                    props = await props
                print(f"  bacnet_properties: {props}")

        except Exception as e:
            print(f"  Error: {e}")

    # Disconnect
    if device:
        device.disconnect()
    await bacnet._disconnect()
    print("\nDone!")

if __name__ == "__main__":
    asyncio.run(diagnose())

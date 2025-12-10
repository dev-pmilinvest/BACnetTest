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
    try:
        device = await BAC0.device(target, device_id, bacnet)
        print(f"Connected to device: {device.properties.name}")
        print(f"\nAvailable points:")
        for point in device.points:
            print(f"  - {point.properties.name} ({point.properties.type}:{point.properties.address})")

            # Check if point has priority array info
            if hasattr(point, 'priority_array'):
                print(f"    Priority Array: {point.priority_array}")
            if hasattr(point, 'bacnet_properties'):
                print(f"    Properties: {point.bacnet_properties}")
    except Exception as e:
        print(f"Could not create device object: {e}")

    # Try direct reads on analogValue:1
    print(f"\n{'='*60}")
    print("Testing direct property reads on analogValue:1")
    print(f"{'='*60}\n")

    test_properties = [
        ('presentValue', 'Present Value'),
        ('priorityArray', 'Priority Array (by name)'),
        ('87', 'Priority Array (by ID 87)'),
        ('relinquishDefault', 'Relinquish Default'),
        ('objectName', 'Object Name'),
        ('objectType', 'Object Type'),
        ('propertyList', 'Property List'),
    ]

    for prop, desc in test_properties:
        try:
            point = f"{target} analogValue 1 {prop}"
            result = await bacnet.read(point)
            print(f"  {desc}: {result}")
            if hasattr(result, 'dict_contents'):
                print(f"    dict_contents(): {result.dict_contents()}")
            if hasattr(result, '__iter__') and not isinstance(result, str):
                print(f"    iterable length: {len(list(result))}")
        except Exception as e:
            print(f"  {desc}: ERROR - {e}")

    # Check what the actual object type is
    print(f"\n{'='*60}")
    print("Reading objectType to verify the object exists")
    print(f"{'='*60}\n")

    for obj_type in ['analogValue', 'analogInput', 'analogOutput']:
        try:
            point = f"{target} {obj_type} 1 objectName"
            result = await bacnet.read(point)
            print(f"  {obj_type}:1 objectName = {result}")
        except Exception as e:
            print(f"  {obj_type}:1 - {e}")

    # Disconnect
    await bacnet._disconnect()
    print("\nDone!")

if __name__ == "__main__":
    asyncio.run(diagnose())

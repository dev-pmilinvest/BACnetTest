"""
Diagnostic script to explore BACnet device properties
"""
import asyncio
import BAC0


def parse_priority_value(pv):
    """Parse a single PriorityValue object"""
    # Try dict_contents first
    if hasattr(pv, 'dict_contents'):
        d = pv.dict_contents()
        if isinstance(d, dict):
            keys = list(d.keys())
            if keys:
                key = keys[0]
                if key == 'null' or key is None:
                    return None
                val = d[key]
                try:
                    return float(val) if val is not None else None
                except (ValueError, TypeError):
                    return val

    # Try direct attribute access
    if hasattr(pv, 'null'):
        return None
    if hasattr(pv, 'real'):
        return pv.real
    if hasattr(pv, 'integer'):
        return pv.integer

    # Try string conversion
    s = str(pv)
    if 'null' in s.lower():
        return None

    return str(pv)


def parse_priority_array(pa):
    """Parse PriorityArray into list of values"""
    result = []
    active_priority = None

    if pa is None:
        return None, None

    # If it's iterable, iterate
    if hasattr(pa, '__iter__'):
        for i, pv in enumerate(pa):
            val = parse_priority_value(pv)
            result.append(val)
            if val is not None and active_priority is None:
                active_priority = i + 1  # 1-indexed

    return result, active_priority


async def diagnose():
    # Connect to BACnet
    bacnet = BAC0.start(ip='192.168.1.18/24', port=47809)
    await asyncio.sleep(2)

    target = "192.168.1.43:47808"
    device_id = 128143

    print(f"\n{'='*60}")
    print(f"Diagnosing BACnet device at {target} (ID: {device_id})")
    print(f"{'='*60}\n")

    # Test with CORRECT instance IDs from the device
    print("Testing priority array parsing")
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

        # Read priorityArray
        try:
            point = f"{target} {obj_type} {instance} priorityArray"
            result = await bacnet.read(point)

            print(f"  Raw priorityArray type: {type(result)}")

            # Check first element
            if result and hasattr(result, '__iter__'):
                first = list(result)[0]
                print(f"  First PriorityValue type: {type(first)}")
                print(f"  First PriorityValue str: {first}")
                if hasattr(first, 'dict_contents'):
                    print(f"  First PriorityValue dict_contents: {first.dict_contents()}")
                if hasattr(first, '__dict__'):
                    print(f"  First PriorityValue __dict__: {first.__dict__}")

                # Check what attributes exist
                attrs = [a for a in dir(first) if not a.startswith('_')]
                print(f"  First PriorityValue attrs: {attrs[:10]}...")  # First 10

            # Parse it
            pa_list, active = parse_priority_array(result)
            print(f"  Parsed priority_array: {pa_list}")
            print(f"  Active priority: {active}")

        except Exception as e:
            print(f"  priorityArray: ERROR - {e}")
            import traceback
            traceback.print_exc()

    # Disconnect
    await bacnet._disconnect()
    print("\nDone!")

if __name__ == "__main__":
    asyncio.run(diagnose())

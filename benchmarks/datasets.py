import random
import string
import uuid
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

import orjson


def generate_random_string(length: int) -> str:
    return "".join(random.choices(string.ascii_letters + string.digits, k=length))


def get_json_size(doc: dict[str, Any]) -> int:
    return len(orjson.dumps(doc))


def generate_flat_document(target_size: int) -> dict[str, Any]:
    doc = {
        "id": str(uuid.uuid4()),
        "timestamp": datetime.now().isoformat(),
        "version": 1,
        "active": True,
        "score": random.uniform(0, 100),
        "count": random.randint(1, 1000),
    }

    current_size = get_json_size(doc)
    field_counter = 0

    # Use larger batches for better performance
    while current_size < target_size:
        remaining = target_size - current_size

        # Add multiple fields at once before checking size
        batch_size = min(100, max(10, remaining // 1000))

        for _ in range(batch_size):
            if current_size >= target_size:
                break

            field_name = f"field_{field_counter}"

            if field_counter % 5 == 0:
                # Add string field - estimate size needed
                string_length = min(max(remaining // 20, 10), 500)
                doc[field_name] = generate_random_string(string_length)
            elif field_counter % 5 == 1:
                doc[field_name] = random.uniform(-1000, 1000)
            elif field_counter % 5 == 2:
                doc[field_name] = random.choice([True, False])
            elif field_counter % 5 == 3:
                doc[field_name] = [random.randint(1, 100) for _ in range(random.randint(1, 10))]
            else:
                doc[field_name] = (datetime.now() + timedelta(days=random.randint(-365, 365))).isoformat()

            field_counter += 1

            # Safety check
            if field_counter > 50000:
                break

        # Check size only after adding a batch
        current_size = get_json_size(doc)

    # Final guarantee: ensure we meet the target size
    current_size = get_json_size(doc)
    if current_size < target_size:
        remaining = target_size - current_size
        # Add final filler to guarantee target size
        doc["size_guarantee"] = generate_random_string(remaining + 10)

    return doc


def generate_nested_document(target_size: int, max_depth: int = 5) -> dict[str, Any]:
    def create_nested_object(depth: int, target_obj_size: int) -> dict[str, Any]:
        if depth >= max_depth or target_obj_size < 100:
            # Use most of the target size for the string value
            string_length = max(target_obj_size // 2, 10)
            return {"value": generate_random_string(string_length)}

        obj = {
            "level": depth,
            "id": str(uuid.uuid4()),
            "data": generate_random_string(50),
        }

        if depth < max_depth - 1:
            # Be more conservative with base object size estimation
            base_size = 150  # More accurate base size
            remaining_size = max(target_obj_size - base_size, 100)

            if remaining_size > 300:
                # Add nested object (50% of remaining size)
                nested_size = remaining_size // 2
                obj["nested"] = create_nested_object(depth + 1, nested_size)

                # Add array of nested objects (remaining 50%)
                array_remaining = remaining_size - nested_size
                if array_remaining > 150:
                    array_count = max(1, min(array_remaining // 400, 2))
                    obj_size_per_item = array_remaining // array_count
                    obj["array"] = [create_nested_object(depth + 1, obj_size_per_item) for _ in range(array_count)]

        # Check current size and add substantial filler if needed
        current_size = get_json_size(obj)
        if current_size < target_obj_size:
            remaining = target_obj_size - current_size
            if remaining > 50:
                # Add multiple filler strings to ensure we reach the target
                filler_count = 0
                while current_size < target_obj_size and filler_count < 5:
                    remaining = target_obj_size - current_size
                    if remaining <= 30:
                        break
                    # Use 80% of remaining size for filler
                    filler_size = max(remaining * 4 // 5, 10)
                    obj[f"filler_{filler_count}"] = generate_random_string(filler_size)
                    current_size = get_json_size(obj)
                    filler_count += 1

        return obj

    doc = create_nested_object(0, target_size)

    # Final guarantee: ensure we meet the target size
    current_size = get_json_size(doc)
    if current_size < target_size:
        remaining = target_size - current_size
        # Add final filler to guarantee target size
        doc["size_guarantee"] = generate_random_string(remaining + 10)

    return doc


def generate_array_heavy_document(target_size: int) -> dict[str, Any]:
    doc: dict[str, Any] = {
        "id": str(uuid.uuid4()),
        "type": "array_heavy",
        "created": datetime.now().isoformat(),
    }

    current_size = get_json_size(doc)

    # Pre-calculate approximate sizes for each data type
    int_size = 4  # approximate bytes per integer
    float_size = 8  # approximate bytes per float
    bool_size = 5  # approximate bytes per boolean

    while current_size < target_size:
        remaining = target_size - current_size

        # Add large batches based on remaining size
        if remaining > 50000:
            # Large batches for big remaining sizes
            batch_integers = min(5000, remaining // int_size // 10)
            batch_floats = min(3000, remaining // float_size // 10)
            batch_strings = min(1000, remaining // 100)
            batch_booleans = min(10000, remaining // bool_size // 10)
        elif remaining > 5000:
            # Medium batches
            batch_integers = min(1000, remaining // int_size // 5)
            batch_floats = min(500, remaining // float_size // 5)
            batch_strings = min(200, remaining // 100)
            batch_booleans = min(2000, remaining // bool_size // 5)
        else:
            # Small batches
            batch_integers = min(100, remaining // int_size)
            batch_floats = min(50, remaining // float_size)
            batch_strings = min(20, remaining // 100)
            batch_booleans = min(200, remaining // bool_size)

        # Add all arrays in one go
        arrays = {
            "integers": [random.randint(1, 1000) for _ in range(batch_integers)],
            "floats": [random.uniform(0, 1000) for _ in range(batch_floats)],
            "strings": [generate_random_string(20) for _ in range(batch_strings)],
            "booleans": [random.choice([True, False]) for _ in range(batch_booleans)],
            "dates": [(datetime.now() + timedelta(days=i)).isoformat() for i in range(min(batch_strings, 100))],
            "mixed": [
                random.choice([random.randint(1, 100), generate_random_string(10), random.choice([True, False]), None])
                for _ in range(min(batch_integers // 2, 1000))
            ],
            "nested_arrays": [
                [random.randint(1, 10) for _ in range(random.randint(1, 5))]
                for _ in range(min(batch_integers // 10, 100))
            ],
        }

        # Update document with new arrays
        for key, value in arrays.items():
            if key in doc:
                doc[key].extend(value)
            else:
                doc[key] = value

        # Check size after adding entire batch
        new_size = get_json_size(doc)
        if new_size <= current_size:
            # If no progress, add a large filler string
            remaining = target_size - current_size
            if remaining > 100:
                filler_size = remaining // 2
                doc["emergency_filler"] = generate_random_string(filler_size)
            break

        current_size = new_size

    # Final guarantee: ensure we meet the target size
    current_size = get_json_size(doc)
    if current_size < target_size:
        remaining = target_size - current_size
        # Add final filler to guarantee target size
        doc["size_guarantee"] = generate_random_string(remaining + 10)

    return doc


def generate_test_datasets() -> dict[str, dict[str, Any]]:
    datasets = {}

    sizes = [
        ("1kb", 1024),
        ("10kb", 10240),
        ("100kb", 102400),
        ("1mb", 1048576),
        ("10mb", 10485760),
    ]

    for size_name, size_bytes in sizes:
        print(f"Generating {size_name} datasets...")

        datasets[f"{size_name}_flat"] = generate_flat_document(size_bytes)
        datasets[f"{size_name}_nested"] = generate_nested_document(size_bytes)
        datasets[f"{size_name}_array_heavy"] = generate_array_heavy_document(size_bytes)

    return datasets


def save_datasets(datasets: dict[str, dict[str, Any]], output_dir: Path) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)

    for name, data in datasets.items():
        file_path = output_dir / f"{name}.json"
        print(f"Saving {name} to {file_path}...")

        # Use orjson for faster file writing
        with open(file_path, "wb") as f:
            f.write(orjson.dumps(data, option=orjson.OPT_INDENT_2))

        # Get file size and JSON size
        file_size = file_path.stat().st_size
        json_size = get_json_size(data)

        print(f"  - File size: {file_size:,} bytes")
        print(f"  - JSON size: {json_size:,} bytes")
        print()


def ensure_datasets() -> None:
    output_dir = Path(__file__).parent / "data"
    output_dir.mkdir(parents=True, exist_ok=True)

    if len(list(output_dir.glob("*.json"))):
        return

    print("Generating test datasets...")

    datasets = generate_test_datasets()

    save_datasets(datasets, output_dir)

    print(f"Total {len(datasets)} datasets generated!")
    print("All datasets should be larger than their target sizes.")


def load_datasets() -> dict[str, dict[str, Any]]:
    output_dir = Path(__file__).parent / "data"
    return {file.stem: orjson.loads(file.read_bytes()) for file in output_dir.glob("*.json")}


if __name__ == "__main__":
    ensure_datasets()

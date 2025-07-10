# lbson - Fast BSON Library for Python

[![PyPI version](https://badge.fury.io/py/lbson-py.svg)](https://badge.fury.io/py/lbson-py)
[![Python versions](https://img.shields.io/pypi/pyversions/lbson-py.svg)](https://pypi.org/project/lbson-py/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![CI](https://github.com/Soju06/lbson/workflows/CI/badge.svg)](https://github.com/Soju06/lbson/actions/workflows/ci.yml)

A high-performance BSON (Binary JSON) encoding and decoding library for Python, built with C++ for maximum speed. This library enables you to work with BSON data without requiring MongoDB drivers, making it perfect for standalone applications, data processing pipelines, and microservices.

## ✨ Key Features

- **🚀 High Performance**: C++ implementation with Python bindings using pybind11
- **🔧 Zero Dependencies**: No MongoDB driver required - works standalone
- **🎯 Multiple Modes**: Support for Python native, JSON, and Extended JSON decoding modes
- **🛡️ Safe by Default**: Built-in circular reference detection and configurable limits
- **📦 Complete BSON Support**: All standard BSON types including ObjectId, DateTime, Binary, UUID, Regex
- **⚡ Memory Efficient**: Streaming operations with minimal memory footprint

## 🚀 Quick Start

### Installation

```bash
pip install lbson-py
```

### Basic Usage

```python
import lbson
from datetime import datetime
import uuid

# Encode Python objects to BSON
data = {
    "name": "John Doe",
    "age": 30,
    "email": "john@example.com",
    "active": True,
    "created_at": datetime.now(),
    "user_id": uuid.uuid4(),
    "scores": [85, 92, 78, 96],
    "metadata": {
        "source": "api",
        "version": "1.2.3"
    }
}

# Encode to BSON bytes
bson_data = lbson.encode(data)
print(f"Encoded size: {len(bson_data)} bytes")

# Decode back to Python objects
decoded_data = lbson.decode(bson_data)
print(decoded_data)
```

## 📚 Comprehensive Guide

### Encoding Options

The `encode()` function supports various options for controlling the encoding behavior:

```python
import lbson

data = {"name": "Alice", "values": [1, 2, 3]}

# Basic encoding
bson_data = lbson.encode(data)

# With options
bson_data = lbson.encode(
    data,
    sort_keys=True,           # Sort dictionary keys
    check_circular=True,      # Detect circular references (default)
    allow_nan=True,          # Allow NaN values (default)
    skipkeys=False,          # Skip unsupported key types
    max_depth=100,           # Maximum nesting depth
    max_size=1024*1024       # Maximum document size (1MB)
)
```

### Decoding Modes

Choose the decoding mode that best fits your use case:

#### Python Mode (Default)
Preserves Python types and provides the most accurate representation:

```python
from datetime import datetime
import uuid

data = {
    "timestamp": datetime.now(),
    "user_id": uuid.uuid4(),
    "count": 42
}

bson_data = lbson.encode(data)
result = lbson.decode(bson_data, mode="python")

print(type(result["timestamp"]))  # <class 'datetime.datetime'>
print(type(result["user_id"]))    # <class 'uuid.UUID'>
```

#### JSON Mode
Converts all types to JSON-compatible format:

```python
result = lbson.decode(bson_data, mode="json")

print(type(result["timestamp"]))  # <class 'str'>
print(type(result["user_id"]))    # <class 'str'>
```

#### Extended JSON Mode
Uses MongoDB's Extended JSON format for type preservation:

```python
result = lbson.decode(bson_data, mode="extended_json")

print(result["timestamp"])  # {"$date": "2023-12-07T15:30:45.123Z"}
print(result["user_id"])    # {"$uuid": "550e8400-e29b-41d4-a716-446655440000"}
```

### Supported Data Types

lbson supports all standard BSON types:

| Python Type | BSON Type | Notes |
|-------------|-----------|--------|
| `dict` | Document | Nested objects supported |
| `list`, `tuple` | Array | Converts tuples to arrays |
| `str` | String | UTF-8 encoded |
| `bytes` | Binary | Raw binary data |
| `int` | Int32/Int64 | Automatic size detection |
| `float` | Double | IEEE 754 double precision |
| `bool` | Boolean | True/False values |
| `None` | Null | Python None |
| `str` | ObjectId | MongoDB ObjectId |
| `datetime.datetime` | DateTime | UTC timestamps |
| `uuid.UUID` | Binary | UUID subtype |
| `re.Pattern` | Regex | Compiled regex patterns |

### Advanced Examples

#### Working with Binary Data

```python
import lbson

# Binary data
binary_data = {
    "file_content": b"Hello, World!",
    "checksum": bytes.fromhex("deadbeef"),
    "metadata": {
        "size": 13,
        "type": "text/plain"
    }
}

bson_data = lbson.encode(binary_data)
decoded = lbson.decode(bson_data)
```

#### Handling Large Documents

```python
import lbson

# Large document with size and depth limits
large_data = {
    "users": [{"id": i, "name": f"User {i}"} for i in range(1000)]
}

try:
    bson_data = lbson.encode(
        large_data,
        max_size=512*1024,      # 512KB limit
        max_depth=10            # Maximum nesting depth
    )
except ValueError as e:
    print(f"Document too large: {e}")
```

### Performance Tips

1. **Disable circular checking** for trusted data:
   ```python
   bson_data = lbson.encode(data, check_circular=False)
   ```

2. **Use appropriate decoding modes**:
   - Use `"python"` mode for Python-to-Python serialization
   - Use `"json"` mode when you need JSON compatibility
   - Use `"extended_json"` for MongoDB compatibility

## 🔧 API Reference

### `lbson.encode(obj, **options) -> bytes`

Encode a Python object to BSON bytes.

**Parameters:**
- `obj` (Any): The Python object to encode
- `skipkeys` (bool): Skip unsupported key types (default: False)
- `check_circular` (bool): Enable circular reference detection (default: True)
- `allow_nan` (bool): Allow NaN/Infinity values (default: True)
- `sort_keys` (bool): Sort dictionary keys (default: False)
- `max_depth` (int|None): Maximum recursion depth (default: None)
- `max_size` (int|None): Maximum document size in bytes (default: None)

**Returns:** BSON-encoded bytes

**Raises:**
- `TypeError`: Unsupported object type
- `ValueError`: Circular reference or invalid value
- `MemoryError`: Document exceeds size limits

### `lbson.decode(data, **options) -> dict`

Decode BSON bytes to a Python object.

**Parameters:**
- `data` (bytes): BSON data to decode
- `mode` (str): Decoding mode - "python", "json", or "extended_json" (default: "python")
- `max_depth` (int|None): Maximum recursion depth (default: None)

**Returns:** Decoded Python dictionary

**Raises:**
- `ValueError`: Malformed BSON data or depth exceeded
- `TypeError`: Invalid input type

## 🏗️ Building from Source

### Prerequisites

- Python 3.9+
- CMake 3.15+
- C++20 compatible compiler
- pybind11

### Build Instructions

```bash
# Clone the repository
git clone https://github.com/Soju06/lbson.git
cd python-bson

# Install lbson
make install
```

### Development Setup

```bash
# Install development build dependencies
make build

# Run tests
make test

# Run benchmarks
make benchmark
```

## 📊 Performance

<img src="benchmarks/images/roundtrip_avg_throughput.png">

| Operation   | Benchmark                       |   lbson (ops/s) |   PyMongo (ops/s) |   bson (ops/s) | lbson vs PyMongo   | lbson vs bson   |
|-------------|---------------------------------|-----------------|-------------------|----------------|--------------------|-----------------|
| roundtrip   | encode_decode_10kb_array_heavy  |           12472 |              6153 |            370 | 2.03× faster       | 33.71× faster   |
| roundtrip   | encode_decode_1mb_array_heavy   |             194 |                96 |              6 | 2.02× faster       | 32.33× faster   |
| roundtrip   | encode_decode_100kb_array_heavy |            1904 |               962 |             58 | 1.98× faster       | 32.83× faster   |
| roundtrip   | encode_decode_1kb_array_heavy   |           48360 |             25224 |           1493 | 1.92× faster       | 32.39× faster   |
| roundtrip   | encode_decode_10mb_array_heavy  |              17 |                 9 |              1 | 1.89× faster       | 17.00× faster   |

<details>
<summary>Benchmark Details</summary>

<img src="benchmarks/images/encode_avg_throughput.png">
<img src="benchmarks/images/decode_avg_throughput.png">

| Operation   | Benchmark                       |   lbson (ops/s) |   PyMongo (ops/s) |   bson (ops/s) | lbson vs PyMongo   | lbson vs bson   |
|-------------|---------------------------------|-----------------|-------------------|----------------|--------------------|-----------------|
| decode      | decode_100kb_array_heavy        |            3612 |              3093 |            159 | 1.17× faster       | 22.72× faster   |
| decode      | decode_100kb_flat               |            4963 |              8171 |            751 | 0.61× faster       | 6.61× faster    |
| decode      | decode_100kb_nested             |           12671 |             14105 |           1559 | 0.90× faster       | 8.13× faster    |
| decode      | decode_10kb_array_heavy         |           22837 |             19378 |           1011 | 1.18× faster       | 22.59× faster   |
| decode      | decode_10kb_flat                |           35846 |             53960 |           4224 | 0.66× faster       | 8.49× faster    |
| decode      | decode_10kb_nested              |           39423 |             41799 |           3855 | 0.94× faster       | 10.23× faster   |
| decode      | decode_10mb_array_heavy         |              33 |                30 |              2 | 1.10× faster       | 16.50× faster   |
| decode      | decode_10mb_flat                |              35 |                55 |              8 | 0.64× faster       | 4.38× faster    |
| decode      | decode_10mb_nested              |             594 |               602 |            414 | 0.99× faster       | 1.43× faster    |
| decode      | decode_1kb_array_heavy          |           90415 |             80836 |           4072 | 1.12× faster       | 22.20× faster   |
| decode      | decode_1kb_flat                 |          153838 |            236909 |          20080 | 0.65× faster       | 7.66× faster    |
| decode      | decode_1kb_nested               |          374800 |            488637 |          64522 | 0.77× faster       | 5.81× faster    |
| decode      | decode_1mb_array_heavy          |             385 |               337 |             15 | 1.14× faster       | 25.67× faster   |
| decode      | decode_1mb_flat                 |             488 |               797 |             80 | 0.61× faster       | 6.10× faster    |
| decode      | decode_1mb_nested               |            4904 |              5343 |           1126 | 0.92× faster       | 4.36× faster    |
| encode      | encode_100kb_array_heavy        |            4286 |              1389 |             91 | 3.09× faster       | 47.10× faster   |
| encode      | encode_100kb_flat               |           18709 |              6848 |            513 | 2.73× faster       | 36.47× faster   |
| encode      | encode_100kb_nested             |           36471 |             13399 |            985 | 2.72× faster       | 37.03× faster   |
| encode      | encode_10kb_array_heavy         |           28458 |              9045 |            585 | 3.15× faster       | 48.65× faster   |
| encode      | encode_10kb_flat                |           95217 |             38317 |           2837 | 2.48× faster       | 33.56× faster   |
| encode      | encode_10kb_nested              |           93763 |             36864 |           2678 | 2.54× faster       | 35.01× faster   |
| encode      | encode_10mb_array_heavy         |              36 |                13 |              1 | 2.77× faster       | 36.00× faster   |
| encode      | encode_10mb_flat                |             170 |                68 |              5 | 2.50× faster       | 34.00× faster   |
| encode      | encode_10mb_nested              |             465 |               372 |             85 | 1.25× faster       | 5.47× faster    |
| encode      | encode_1kb_array_heavy          |          106657 |             37554 |           2434 | 2.84× faster       | 43.82× faster   |
| encode      | encode_1kb_flat                 |          297390 |            163006 |          13583 | 1.82× faster       | 21.89× faster   |
| encode      | encode_1kb_nested               |          481591 |            398013 |          43375 | 1.21× faster       | 11.10× faster   |
| encode      | encode_1mb_array_heavy          |             404 |               136 |              9 | 2.97× faster       | 44.89× faster   |
| encode      | encode_1mb_flat                 |            2043 |               732 |             55 | 2.79× faster       | 37.15× faster   |
| encode      | encode_1mb_nested               |           13130 |              6431 |            525 | 2.04× faster       | 25.01× faster   |
| roundtrip   | encode_decode_100kb_array_heavy |            1904 |               962 |             58 | 1.98× faster       | 32.83× faster   |
| roundtrip   | encode_decode_100kb_flat        |            3889 |              3694 |            305 | 1.05× faster       | 12.75× faster   |
| roundtrip   | encode_decode_100kb_nested      |            9141 |              6732 |            591 | 1.36× faster       | 15.47× faster   |
| roundtrip   | encode_decode_10kb_array_heavy  |           12472 |              6153 |            370 | 2.03× faster       | 33.71× faster   |
| roundtrip   | encode_decode_10kb_flat         |           25533 |             21864 |           1662 | 1.17× faster       | 15.36× faster   |
| roundtrip   | encode_decode_10kb_nested       |           27376 |             19352 |           1537 | 1.41× faster       | 17.81× faster   |
| roundtrip   | encode_decode_10mb_array_heavy  |              17 |                 9 |              1 | 1.89× faster       | 17.00× faster   |
| roundtrip   | encode_decode_10mb_flat         |              28 |                30 |              3 | 0.93× faster       | 9.33× faster    |
| roundtrip   | encode_decode_10mb_nested       |             242 |               185 |             60 | 1.31× faster       | 4.03× faster    |
| roundtrip   | encode_decode_1kb_array_heavy   |           48360 |             25224 |           1493 | 1.92× faster       | 32.39× faster   |
| roundtrip   | encode_decode_1kb_flat          |           97414 |             94199 |           7550 | 1.03× faster       | 12.90× faster   |
| roundtrip   | encode_decode_1kb_nested        |          207828 |            211679 |          22397 | 0.98× faster       | 9.28× faster    |
| roundtrip   | encode_decode_1mb_array_heavy   |             194 |                96 |              6 | 2.02× faster       | 32.33× faster   |
| roundtrip   | encode_decode_1mb_flat          |             390 |               374 |             33 | 1.04× faster       | 11.82× faster   |
| roundtrip   | encode_decode_1mb_nested        |            3532 |              2610 |            347 | 1.35× faster       | 10.18× faster   |
</details>


## 📚 Related Projects

- [pymongo](https://github.com/mongodb/mongo-python-driver) - Official MongoDB Python driver
- [bson](https://pypi.org/project/bson/) - Pure Python BSON implementation

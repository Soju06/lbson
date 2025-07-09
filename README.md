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

Coming soon...

## 📚 Related Projects

- [pymongo](https://github.com/mongodb/mongo-python-driver) - Official MongoDB Python driver
- [bson](https://pypi.org/project/bson/) - Pure Python BSON implementation

"""
lbson - Fast BSON Library for Python

This library provides high-performance BSON (Binary JSON) encoding and decoding
functionality for Python applications without requiring MongoDB drivers.
"""

import typing

from ._core import DecoderMode
from ._core import decode as _core_decode
from ._core import encode as _core_encode
from ._version import __version__, __version_tuple__


def encode(
    obj: typing.Any,
    *,
    skipkeys: bool = False,
    check_circular: bool = True,
    allow_nan: bool = True,
    sort_keys: bool = False,
    max_depth: typing.Optional[int] = None,
    max_size: typing.Optional[int] = None,
    **kw,
) -> bytes:
    """
    Encode a Python object to BSON bytes.

    Args:
        obj: The Python object to encode. Only dict type is supported.

        skipkeys: If True, skip dictionary keys that are not of basic types
            (str, int, float, bool, None) instead of raising TypeError.
            Default: False

        check_circular: If True, detect and prevent circular references in
            nested objects. Disable for better performance if you're certain
            there are no circular references. Default: True

        allow_nan: If True, allow NaN, Infinity, and -Infinity float values.
            If False, raise ValueError for these values. Default: True

        sort_keys: If True, sort dictionary keys in the output. This can be
            useful for reproducible output. Default: False

        max_depth: Maximum recursion depth for nested objects. None means
            no limit (uses system default). Default: None

        max_size: Maximum size of the resulting BSON document in bytes.
            None means no limit (uses system default). Default: None

    Returns:
        bytes: The BSON-encoded data as bytes

    Raises:
        TypeError: If the object contains unsupported types
        ValueError: If circular references are detected (when check_circular=True)
            or if NaN values are encountered (when allow_nan=False)
        MemoryError: If the encoded data exceeds max_size

    Examples:
        Basic usage:

        >>> import lbson
        >>> data = {"name": "Alice", "scores": [85, 92, 78]}
        >>> bson_data = lbson.encode(data)
        >>> type(bson_data)
        <class 'bytes'>

        With options:

        >>> # Sort keys and limit depth
        >>> bson_data = lbson.encode(data, sort_keys=True, max_depth=10)

        >>> # Skip invalid keys instead of raising errors
        >>> data_with_complex_keys = {complex(1, 2): "value"}
        >>> bson_data = lbson.encode(data_with_complex_keys, skipkeys=True)
    """
    return _core_encode(
        obj,
        skipkeys=skipkeys,
        check_circular=check_circular,
        allow_nan=allow_nan,
        sort_keys=sort_keys,
        max_depth=max_depth or 2147483647,
        max_size=max_size or 2147483647,
    )


def decode(
    data: bytes,
    *,
    mode: typing.Literal["json", "extended_json", "python"] = "python",
    max_depth: typing.Optional[int] = None,
    **kw,
) -> dict:
    """Decode BSON bytes to a Python object.

    This function converts BSON (Binary JSON) data back to Python objects.
    The decoding behavior can be controlled through different modes to match
    your application's requirements.

    Args:
        data: The BSON data to decode as bytes

        mode: Decoding mode that determines how BSON types are converted:
            - "python" (default): Convert to native Python types where possible.
              This preserves the most type information and is recommended for
              Python-to-Python serialization.

            - "json": Convert to JSON-compatible types only. Complex types like
              datetime, ObjectId, etc. are converted to strings or simple dicts.
              Use this when you need JSON serialization compatibility.

            - "extended_json": Convert to MongoDB Extended JSON format. This
              maintains type information using MongoDB's Extended JSON specification
              (e.g., {"$date": "2023-01-01T00:00:00Z"} for datetime objects).

        max_depth: Maximum recursion depth for nested objects. None means
            no limit (uses system default). Default: None

    Returns:
        dict: The decoded Python object (always a dictionary for BSON documents)

    Raises:
        ValueError: If the BSON data is malformed, corrupted, or exceeds max_depth
        TypeError: If the data parameter is not bytes

    Examples:
        Basic decoding:

        >>> import lbson
        >>> bson_data = lbson.encode({"name": "Bob", "age": 25})
        >>> decoded = lbson.decode(bson_data)
        >>> print(decoded)
        {'name': 'Bob', 'age': 25}

        Different modes:

        >>> from datetime import datetime
        >>> data = {"created": datetime.now(), "count": 42}
        >>> bson_data = lbson.encode(data)

        >>> # Python mode preserves datetime objects
        >>> result = lbson.decode(bson_data, mode="python")
        >>> type(result["created"])
        <class 'datetime.datetime'>

        >>> # JSON mode converts to string
        >>> result = lbson.decode(bson_data, mode="json")
        >>> type(result["created"])
        <class 'str'>

        >>> # Extended JSON mode uses MongoDB format
        >>> result = lbson.decode(bson_data, mode="extended_json")
        >>> result["created"]
        {'$date': '2023-12-07T15:30:45.123Z'}

        With depth limiting:

        >>> result = lbson.decode(bson_data, max_depth=5)
    """
    if mode == "python":
        enc_mode = DecoderMode.PYTHON
    elif mode == "json":
        enc_mode = DecoderMode.JSON
    elif mode == "extended_json":
        enc_mode = DecoderMode.EXTENDED_JSON
    else:
        raise ValueError(f"Invalid mode: {mode}. Must be one of: 'python', 'json', 'extended_json'")

    return _core_decode(data, mode=enc_mode, max_depth=max_depth or 2147483647)


__all__ = ["encode", "decode", "__version__", "__version_tuple__"]

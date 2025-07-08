import base64
import datetime
import math
import re
import sys
import uuid

import pytest

import lbson


def patch_utc_isoformat(value: str) -> str:
    if sys.version_info < (3, 11):
        return value.replace("Z", "+00:00")

    return value


class TestDecodeBasicTypes:
    def test_decode_none_field(self) -> None:
        assert lbson.decode(bytes.fromhex("0b0000000a6e6f6e650000")) == {"none": None}

    def test_decode_bool_field(self) -> None:
        assert lbson.decode(bytes.fromhex("0c00000008626f6f6c000100")) == {"bool": True}
        assert lbson.decode(bytes.fromhex("0c00000008626f6f6c000000")) == {"bool": False}

    def test_decode_int32_field(self) -> None:
        assert lbson.decode(bytes.fromhex("1000000010696e743332000100000000")) == {"int32": 1}
        assert lbson.decode(bytes.fromhex("1000000010696e74333200ffffffff00")) == {"int32": -1}
        assert lbson.decode(bytes.fromhex("1000000010696e74333200ffffff7f00")) == {"int32": 2147483647}
        assert lbson.decode(bytes.fromhex("1000000010696e743332000000008000")) == {"int32": -2147483648}

    def test_decode_int64_field(self) -> None:
        assert lbson.decode(bytes.fromhex("1400000012696e74363400000000800000000000")) == {"int64": 2147483648}
        assert lbson.decode(bytes.fromhex("1400000012696e74363400ffffff7fffffffff00")) == {"int64": -2147483649}
        assert lbson.decode(bytes.fromhex("1400000012696e74363400ffffffffffffff7f00")) == {"int64": 9223372036854775807}
        assert lbson.decode(bytes.fromhex("1400000012696e74363400000000000000008000")) == {
            "int64": -9223372036854775808
        }

    def test_decode_float_field(self) -> None:
        assert lbson.decode(bytes.fromhex("1500000001646f62756c6500000000000000f03f00")) == {"dobule": 1.0}
        assert lbson.decode(bytes.fromhex("1500000001646f62756c6500182d4454fb21094000")) == {
            "dobule": 3.141592653589793
        }
        assert lbson.decode(bytes.fromhex("1500000001646f62756c6500a0c8eb85f3cce17f00")) == {"dobule": 1e308}
        assert lbson.decode(bytes.fromhex("1500000001646f62756c6500000000000000f07f00")) == {"dobule": math.inf}
        assert lbson.decode(bytes.fromhex("1500000001646f62756c6500000000000000f0ff00")) == {"dobule": -math.inf}
        assert math.isnan(lbson.decode(bytes.fromhex("1500000001646f62756c6500000000000000f87f00"))["dobule"])

    def test_decode_string_field(self) -> None:
        assert lbson.decode(bytes.fromhex("18000000026e616d6500090000004a6f686e20446f650000")) == {"name": "John Doe"}
        assert lbson.decode(bytes.fromhex("10000000026e616d6500010000000000")) == {"name": ""}
        assert lbson.decode(bytes.fromhex("11000000026e616d650002000000000000")) == {"name": "\0"}
        assert lbson.decode(bytes.fromhex("18000000026e616d6500090000004a6f686e00446f650000")) == {"name": "John\0Doe"}

    def test_decode_datetime_field(self) -> None:
        json_datetime = lbson.decode(bytes.fromhex("17000000096461746574696d65008b7eb2cb9701000000"), mode="json")[
            "datetime"
        ]
        assert isinstance(json_datetime, str)
        assert datetime.datetime.fromisoformat(json_datetime) == datetime.datetime(
            2025, 7, 2, 15, 12, 42, 123000, tzinfo=datetime.timezone.utc
        )
        extended_json_datetime = lbson.decode(
            bytes.fromhex("17000000096461746574696d65008b7eb2cb9701000000"), mode="extended_json"
        )["datetime"]
        assert isinstance(extended_json_datetime, dict)
        assert datetime.datetime.fromisoformat(extended_json_datetime["$date"]) == datetime.datetime(
            2025, 7, 2, 15, 12, 42, 123000, tzinfo=datetime.timezone.utc
        )
        assert lbson.decode(bytes.fromhex("17000000096461746574696d65008b7eb2cb9701000000"), mode="python") == {
            "datetime": datetime.datetime(2025, 7, 2, 15, 12, 42, 123000, tzinfo=datetime.timezone.utc)
        }

    def test_decode_regex_field(self) -> None:
        assert lbson.decode(
            bytes.fromhex("1d0000000b7265676578005e5b612d7a412d5a302d395d2b2400750000"), mode="json"
        ) == {"regex": "/^[a-zA-Z0-9]+$/u"}
        assert lbson.decode(
            bytes.fromhex("1d0000000b7265676578005e5b612d7a412d5a302d395d2b2400750000"), mode="extended_json"
        ) == {"regex": {"$regularExpression": {"pattern": "^[a-zA-Z0-9]+$", "options": "u"}}}
        assert lbson.decode(
            bytes.fromhex("1d0000000b7265676578005e5b612d7a412d5a302d395d2b2400750000"), mode="python"
        ) == {"regex": re.compile("^[a-zA-Z0-9]+$")}
        assert lbson.decode(
            bytes.fromhex("1e0000000b7265676578005e5b612d7a412d5a302d395d2b240069750000"), mode="json"
        ) == {"regex": "/^[a-zA-Z0-9]+$/iu"}
        assert lbson.decode(
            bytes.fromhex("1e0000000b7265676578005e5b612d7a412d5a302d395d2b240069750000"), mode="extended_json"
        ) == {"regex": {"$regularExpression": {"pattern": "^[a-zA-Z0-9]+$", "options": "iu"}}}
        assert lbson.decode(
            bytes.fromhex("1e0000000b7265676578005e5b612d7a412d5a302d395d2b240069750000"), mode="python"
        ) == {"regex": re.compile("^[a-zA-Z0-9]+$", re.IGNORECASE)}
        assert lbson.decode(
            bytes.fromhex("1f0000000b7265676578005e5b612d7a412d5a302d395d2b2400696d750000"), mode="json"
        ) == {"regex": "/^[a-zA-Z0-9]+$/imu"}
        assert lbson.decode(
            bytes.fromhex("1f0000000b7265676578005e5b612d7a412d5a302d395d2b2400696d750000"), mode="extended_json"
        ) == {"regex": {"$regularExpression": {"pattern": "^[a-zA-Z0-9]+$", "options": "imu"}}}
        assert lbson.decode(
            bytes.fromhex("1f0000000b7265676578005e5b612d7a412d5a302d395d2b2400696d750000"), mode="python"
        ) == {"regex": re.compile("^[a-zA-Z0-9]+$", re.IGNORECASE | re.MULTILINE)}
        assert lbson.decode(
            bytes.fromhex("200000000b7265676578005e5b612d7a412d5a302d395d2b2400696d73750000"), mode="json"
        ) == {"regex": "/^[a-zA-Z0-9]+$/imsu"}
        assert lbson.decode(
            bytes.fromhex("200000000b7265676578005e5b612d7a412d5a302d395d2b2400696d73750000"), mode="extended_json"
        ) == {"regex": {"$regularExpression": {"pattern": "^[a-zA-Z0-9]+$", "options": "imsu"}}}
        assert lbson.decode(
            bytes.fromhex("200000000b7265676578005e5b612d7a412d5a302d395d2b2400696d73750000"), mode="python"
        ) == {"regex": re.compile("^[a-zA-Z0-9]+$", re.IGNORECASE | re.MULTILINE | re.DOTALL)}

    def test_decode_binary_field(self) -> None:
        assert lbson.decode(
            bytes.fromhex("1f0000000562696e617279000d0000000048656c6c6f2c20576f726c642100"), mode="json"
        ) == {"binary": base64.b64encode(b"Hello, World!").decode()}
        assert lbson.decode(
            bytes.fromhex("1f0000000562696e617279000d0000000048656c6c6f2c20576f726c642100"), mode="extended_json"
        ) == {"binary": {"$binary": {"base64": base64.b64encode(b"Hello, World!").decode(), "subType": "00"}}}
        assert lbson.decode(
            bytes.fromhex("1f0000000562696e617279000d0000000048656c6c6f2c20576f726c642100"), mode="python"
        ) == {"binary": b"Hello, World!"}
        assert lbson.decode(bytes.fromhex("120000000562696e61727900000000000000"), mode="json") == {"binary": ""}
        assert lbson.decode(bytes.fromhex("120000000562696e61727900000000000000"), mode="extended_json") == {
            "binary": {"$binary": {"base64": "", "subType": "00"}}
        }
        assert lbson.decode(bytes.fromhex("120000000562696e61727900000000000000"), mode="python") == {"binary": b""}
        assert lbson.decode(
            bytes.fromhex("210000000562696e617279000f0000000000000000000000000000000000000000"), mode="json"
        ) == {"binary": base64.b64encode(b"\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00").decode()}
        assert lbson.decode(
            bytes.fromhex("210000000562696e617279000f0000000000000000000000000000000000000000"), mode="extended_json"
        ) == {
            "binary": {
                "$binary": {
                    "base64": base64.b64encode(
                        b"\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00"
                    ).decode(),
                    "subType": "00",
                }
            }
        }
        assert lbson.decode(
            bytes.fromhex("210000000562696e617279000f0000000000000000000000000000000000000000"), mode="python"
        ) == {"binary": b"\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00"}
        assert lbson.decode(
            bytes.fromhex("200000000562696e617279000e0000000048656c6c6f2c20576f726c64210000"), mode="json"
        ) == {"binary": base64.b64encode(b"Hello, World!\x00").decode()}
        assert lbson.decode(
            bytes.fromhex("200000000562696e617279000e0000000048656c6c6f2c20576f726c64210000"), mode="extended_json"
        ) == {"binary": {"$binary": {"base64": base64.b64encode(b"Hello, World!\x00").decode(), "subType": "00"}}}
        assert lbson.decode(
            bytes.fromhex("200000000562696e617279000e0000000048656c6c6f2c20576f726c64210000"), mode="python"
        ) == {"binary": b"Hello, World!\x00"}

    def test_decode_uuid_field(self) -> None:
        assert lbson.decode(
            bytes.fromhex("2000000005757569640010000000040657d16c07334f09ae32d778a21c062d00"), mode="json"
        ) == {"uuid": "0657d16c-0733-4f09-ae32-d778a21c062d"}
        assert lbson.decode(
            bytes.fromhex("2000000005757569640010000000040657d16c07334f09ae32d778a21c062d00"), mode="extended_json"
        ) == {"uuid": {"$uuid": "0657d16c-0733-4f09-ae32-d778a21c062d"}}
        assert lbson.decode(
            bytes.fromhex("2000000005757569640010000000040657d16c07334f09ae32d778a21c062d00"), mode="python"
        ) == {"uuid": uuid.UUID("0657d16c-0733-4f09-ae32-d778a21c062d")}

    def test_decode_object_field(self) -> None:
        assert lbson.decode(
            bytes.fromhex("2d000000036f626a6563740020000000106100010000000262000200000042000163006666666666660a400000")
        ) == {"object": {"a": 1, "b": "B", "c": 3.3}}
        assert lbson.decode(
            bytes.fromhex(
                "3e000000036f626a6563740031000000046100290000001030000100000010310002000000103200030000000333000c0000001062000400000000000000"
            )
        ) == {"object": {"a": [1, 2, 3, {"b": 4}]}}
        assert lbson.decode(bytes.fromhex("12000000036f626a65637400050000000000")) == {"object": {}}

    def test_decode_list_field(self) -> None:
        assert lbson.decode(
            bytes.fromhex(
                "90000000046c6973740085000000103000010000000231000200000032000132006666666666660a4010330004000000083400000a350003360020000000106100010000000262000200000042000163006666666666660a40000437000500000000043800290000001030000100000010310002000000103200030000000333000c0000001062000400000000000000"
            )
        ) == {"list": [1, "2", 3.3, 4, False, None, {"a": 1, "b": "B", "c": 3.3}, [], [1, 2, 3, {"b": 4}]]}
        assert lbson.decode(bytes.fromhex("10000000046c69737400050000000000")) == {"list": []}
        assert lbson.decode(
            bytes.fromhex(
                "a8000000046c697374009d000000043000950000000430008d0000000430006d000000043000450000000430000d0000000430000500000000000431002d0000000430000d0000000430000500000000000431000d000000043000050000000000043200050000000000000431000d000000043000050000000000043200050000000004330005000000000004310015000000043000050000000004310005000000000000000000"
            )
        ) == {"list": [[[[[[[]], [[[]], [[]], []]], [[]], [], []], [[], []]]]]}

    def test_decode_complex_document(self) -> None:
        assert lbson.decode(
            bytes.fromhex(
                "5a0100000375736572004f0100000569640010000000040657d16c07334f09ae32d778a21c062d02757365726e616d65000b0000006a6f686e646f653132330002656d61696c00150000006a6f686e2e646f65406578616d706c652e636f6d0009637265617465645f61740010ca2917890100000370726f66696c6500db0000000266697273745f6e616d6500050000004a6f686e00026c6173745f6e616d650004000000446f650010616765002000000004696e7465726573747300340000000230000c00000070686f746f677261706879000231000700000068696b696e670002320007000000636f64696e6700000361646472657373005d00000002737472656574000c000000313233204d61696e205374000263697479000e00000053616e204672616e636973636f0002636f756e74727900040000005553410002706f7374616c5f636f6465000600000039343130350000000000"
            ),
            mode="json",
        ) == {
            "user": {
                "id": "0657d16c-0733-4f09-ae32-d778a21c062d",
                "username": "johndoe123",
                "email": "john.doe@example.com",
                "created_at": patch_utc_isoformat("2023-07-02T15:12:42.000Z"),
                "profile": {
                    "first_name": "John",
                    "last_name": "Doe",
                    "age": 32,
                    "interests": ["photography", "hiking", "coding"],
                    "address": {
                        "street": "123 Main St",
                        "city": "San Francisco",
                        "country": "USA",
                        "postal_code": "94105",
                    },
                },
            }
        }
        assert lbson.decode(
            bytes.fromhex(
                "5a0100000375736572004f0100000569640010000000040657d16c07334f09ae32d778a21c062d02757365726e616d65000b0000006a6f686e646f653132330002656d61696c00150000006a6f686e2e646f65406578616d706c652e636f6d0009637265617465645f61740010ca2917890100000370726f66696c6500db0000000266697273745f6e616d6500050000004a6f686e00026c6173745f6e616d650004000000446f650010616765002000000004696e7465726573747300340000000230000c00000070686f746f677261706879000231000700000068696b696e670002320007000000636f64696e6700000361646472657373005d00000002737472656574000c000000313233204d61696e205374000263697479000e00000053616e204672616e636973636f0002636f756e74727900040000005553410002706f7374616c5f636f6465000600000039343130350000000000"
            ),
            mode="extended_json",
        ) == {
            "user": {
                "id": {"$uuid": "0657d16c-0733-4f09-ae32-d778a21c062d"},
                "username": "johndoe123",
                "email": "john.doe@example.com",
                "created_at": {"$date": patch_utc_isoformat("2023-07-02T15:12:42.000Z")},
                "profile": {
                    "first_name": "John",
                    "last_name": "Doe",
                    "age": 32,
                    "interests": ["photography", "hiking", "coding"],
                    "address": {
                        "street": "123 Main St",
                        "city": "San Francisco",
                        "country": "USA",
                        "postal_code": "94105",
                    },
                },
            }
        }
        assert lbson.decode(
            bytes.fromhex(
                "5a0100000375736572004f0100000569640010000000040657d16c07334f09ae32d778a21c062d02757365726e616d65000b0000006a6f686e646f653132330002656d61696c00150000006a6f686e2e646f65406578616d706c652e636f6d0009637265617465645f61740010ca2917890100000370726f66696c6500db0000000266697273745f6e616d6500050000004a6f686e00026c6173745f6e616d650004000000446f650010616765002000000004696e7465726573747300340000000230000c00000070686f746f677261706879000231000700000068696b696e670002320007000000636f64696e6700000361646472657373005d00000002737472656574000c000000313233204d61696e205374000263697479000e00000053616e204672616e636973636f0002636f756e74727900040000005553410002706f7374616c5f636f6465000600000039343130350000000000"
            ),
            mode="python",
        ) == {
            "user": {
                "id": uuid.UUID("0657d16c-0733-4f09-ae32-d778a21c062d"),
                "username": "johndoe123",
                "email": "john.doe@example.com",
                "created_at": datetime.datetime(2023, 7, 2, 15, 12, 42, tzinfo=datetime.timezone.utc),
                "profile": {
                    "first_name": "John",
                    "last_name": "Doe",
                    "age": 32,
                    "interests": ["photography", "hiking", "coding"],
                    "address": {
                        "street": "123 Main St",
                        "city": "San Francisco",
                        "country": "USA",
                        "postal_code": "94105",
                    },
                },
            }
        }

        assert lbson.decode(
            bytes.fromhex(
                "1e020000036f726465720012020000026f726465725f6964000e0000004f52442d323032332d373834350005637573746f6d65725f69640010000000041657d16c07334f09ae32d778a21c062e096f726465725f6461746500a3a0001189010000046974656d7300dd0000000330006d0000000270726f647563745f6964000900000050524f442d30303100026e616d650014000000576972656c657373204865616470686f6e657300107175616e74697479000200000001756e69745f7072696365008fc2f5285cff584001746f74616c008fc2f5285cff684000033100650000000270726f647563745f6964000900000050524f442d30303200026e616d65000c000000536d61727420576174636800107175616e74697479000100000001756e69745f707269636500a4703d0ad7bf724001746f74616c00a4703d0ad7bf72400000037368697070696e675f61646472657373007300000002726563697069656e7400090000004a6f686e20446f650002737472656574000f000000343536204f616b204176656e756500026369747900090000004e657720596f726b0002636f756e74727900040000005553410002706f7374616c5f636f6465000600000031303030310000037061796d656e740049000000026d6574686f64000c0000006372656469745f636172640002737461747573000a000000636f6d706c657465640001746f74616c5f616d6f756e7400ec51b81e853f7f40000000"
            ),
            mode="json",
        ) == {
            "order": {
                "order_id": "ORD-2023-7845",
                "customer_id": "1657d16c-0733-4f09-ae32-d778a21c062e",
                "order_date": patch_utc_isoformat("2023-07-01T10:30:01.123Z"),
                "items": [
                    {
                        "product_id": "PROD-001",
                        "name": "Wireless Headphones",
                        "quantity": 2,
                        "unit_price": 99.99,
                        "total": 199.98,
                    },
                    {
                        "product_id": "PROD-002",
                        "name": "Smart Watch",
                        "quantity": 1,
                        "unit_price": 299.99,
                        "total": 299.99,
                    },
                ],
                "shipping_address": {
                    "recipient": "John Doe",
                    "street": "456 Oak Avenue",
                    "city": "New York",
                    "country": "USA",
                    "postal_code": "10001",
                },
                "payment": {"method": "credit_card", "status": "completed", "total_amount": 499.97},
            }
        }
        assert lbson.decode(
            bytes.fromhex(
                "1e020000036f726465720012020000026f726465725f6964000e0000004f52442d323032332d373834350005637573746f6d65725f69640010000000041657d16c07334f09ae32d778a21c062e096f726465725f6461746500a3a0001189010000046974656d7300dd0000000330006d0000000270726f647563745f6964000900000050524f442d30303100026e616d650014000000576972656c657373204865616470686f6e657300107175616e74697479000200000001756e69745f7072696365008fc2f5285cff584001746f74616c008fc2f5285cff684000033100650000000270726f647563745f6964000900000050524f442d30303200026e616d65000c000000536d61727420576174636800107175616e74697479000100000001756e69745f707269636500a4703d0ad7bf724001746f74616c00a4703d0ad7bf72400000037368697070696e675f61646472657373007300000002726563697069656e7400090000004a6f686e20446f650002737472656574000f000000343536204f616b204176656e756500026369747900090000004e657720596f726b0002636f756e74727900040000005553410002706f7374616c5f636f6465000600000031303030310000037061796d656e740049000000026d6574686f64000c0000006372656469745f636172640002737461747573000a000000636f6d706c657465640001746f74616c5f616d6f756e7400ec51b81e853f7f40000000"
            ),
            mode="extended_json",
        ) == {
            "order": {
                "order_id": "ORD-2023-7845",
                "customer_id": {"$uuid": "1657d16c-0733-4f09-ae32-d778a21c062e"},
                "order_date": {"$date": patch_utc_isoformat("2023-07-01T10:30:01.123Z")},
                "items": [
                    {
                        "product_id": "PROD-001",
                        "name": "Wireless Headphones",
                        "quantity": 2,
                        "unit_price": 99.99,
                        "total": 199.98,
                    },
                    {
                        "product_id": "PROD-002",
                        "name": "Smart Watch",
                        "quantity": 1,
                        "unit_price": 299.99,
                        "total": 299.99,
                    },
                ],
                "shipping_address": {
                    "recipient": "John Doe",
                    "street": "456 Oak Avenue",
                    "city": "New York",
                    "country": "USA",
                    "postal_code": "10001",
                },
                "payment": {"method": "credit_card", "status": "completed", "total_amount": 499.97},
            }
        }
        assert lbson.decode(
            bytes.fromhex(
                "1e020000036f726465720012020000026f726465725f6964000e0000004f52442d323032332d373834350005637573746f6d65725f69640010000000041657d16c07334f09ae32d778a21c062e096f726465725f6461746500a3a0001189010000046974656d7300dd0000000330006d0000000270726f647563745f6964000900000050524f442d30303100026e616d650014000000576972656c657373204865616470686f6e657300107175616e74697479000200000001756e69745f7072696365008fc2f5285cff584001746f74616c008fc2f5285cff684000033100650000000270726f647563745f6964000900000050524f442d30303200026e616d65000c000000536d61727420576174636800107175616e74697479000100000001756e69745f707269636500a4703d0ad7bf724001746f74616c00a4703d0ad7bf72400000037368697070696e675f61646472657373007300000002726563697069656e7400090000004a6f686e20446f650002737472656574000f000000343536204f616b204176656e756500026369747900090000004e657720596f726b0002636f756e74727900040000005553410002706f7374616c5f636f6465000600000031303030310000037061796d656e740049000000026d6574686f64000c0000006372656469745f636172640002737461747573000a000000636f6d706c657465640001746f74616c5f616d6f756e7400ec51b81e853f7f40000000"
            ),
            mode="python",
        ) == {
            "order": {
                "order_id": "ORD-2023-7845",
                "customer_id": uuid.UUID("1657d16c-0733-4f09-ae32-d778a21c062e"),
                "order_date": datetime.datetime(2023, 7, 1, 10, 30, 1, 123000, tzinfo=datetime.timezone.utc),
                "items": [
                    {
                        "product_id": "PROD-001",
                        "name": "Wireless Headphones",
                        "quantity": 2,
                        "unit_price": 99.99,
                        "total": 199.98,
                    },
                    {
                        "product_id": "PROD-002",
                        "name": "Smart Watch",
                        "quantity": 1,
                        "unit_price": 299.99,
                        "total": 299.99,
                    },
                ],
                "shipping_address": {
                    "recipient": "John Doe",
                    "street": "456 Oak Avenue",
                    "city": "New York",
                    "country": "USA",
                    "postal_code": "10001",
                },
                "payment": {"method": "credit_card", "status": "completed", "total_amount": 499.97},
            }
        }

        assert lbson.decode(
            bytes.fromhex(
                "7d02000003706f737400720200000569640010000000042657d16c07334f09ae32d778a21c062f027469746c65001c000000556e6465727374616e64696e672042534f4e20456e636f64696e670002636f6e74656e74004f00000042534f4e202842696e617279204a534f4e2920697320612062696e6172792d656e636f6465642073657269616c697a6174696f6e206f66204a534f4e2d6c696b6520646f63756d656e74732e2e2e0003617574686f7200570000000569640010000000043657d16c07334f09ae32d778a21c0630026e616d65000c000000416c69636520536d6974680002656d61696c0018000000616c6963652e736d697468406578616d706c652e636f6d0000047461677300370000000230000c00000070726f6772616d6d696e670002310009000000646174616261736500023200080000006d6f6e676f6462000009637265617465645f617400409c00118901000009757064617465645f617400605c47178901000004636f6d6d656e747300c80000000330005b0000000275736572000b000000626f625f77696c736f6e0002636f6e74656e74002100000047726561742061727469636c6521205665727920696e666f726d61746976652e000974696d657374616d700080131c118901000000033100620000000275736572000c0000006361726f6c5f64617669730002636f6e74656e7400270000005468616e6b7320666f72206578706c61696e696e67207468697320736f20636c6561726c7921000974696d657374616d7000a0bd6011890100000000036d65746164617461003100000010766965777300e2040000106c696b6573002d0000000172656164696e675f74696d65000000000000002140000000"
            ),
            mode="json",
        ) == {
            "post": {
                "id": "2657d16c-0733-4f09-ae32-d778a21c062f",
                "title": "Understanding BSON Encoding",
                "content": "BSON (Binary JSON) is a binary-encoded serialization of JSON-like documents...",
                "author": {
                    "id": "3657d16c-0733-4f09-ae32-d778a21c0630",
                    "name": "Alice Smith",
                    "email": "alice.smith@example.com",
                },
                "tags": ["programming", "database", "mongodb"],
                "created_at": patch_utc_isoformat("2023-07-01T10:30:00.000Z"),
                "updated_at": patch_utc_isoformat("2023-07-02T15:45:00.000Z"),
                "comments": [
                    {
                        "user": "bob_wilson",
                        "content": "Great article! Very informative.",
                        "timestamp": patch_utc_isoformat("2023-07-01T11:00:00.000Z"),
                    },
                    {
                        "user": "carol_davis",
                        "content": "Thanks for explaining this so clearly!",
                        "timestamp": patch_utc_isoformat("2023-07-01T12:15:00.000Z"),
                    },
                ],
                "metadata": {"views": 1250, "likes": 45, "reading_time": 8.5},
            }
        }
        assert lbson.decode(
            bytes.fromhex(
                "7d02000003706f737400720200000569640010000000042657d16c07334f09ae32d778a21c062f027469746c65001c000000556e6465727374616e64696e672042534f4e20456e636f64696e670002636f6e74656e74004f00000042534f4e202842696e617279204a534f4e2920697320612062696e6172792d656e636f6465642073657269616c697a6174696f6e206f66204a534f4e2d6c696b6520646f63756d656e74732e2e2e0003617574686f7200570000000569640010000000043657d16c07334f09ae32d778a21c0630026e616d65000c000000416c69636520536d6974680002656d61696c0018000000616c6963652e736d697468406578616d706c652e636f6d0000047461677300370000000230000c00000070726f6772616d6d696e670002310009000000646174616261736500023200080000006d6f6e676f6462000009637265617465645f617400409c00118901000009757064617465645f617400605c47178901000004636f6d6d656e747300c80000000330005b0000000275736572000b000000626f625f77696c736f6e0002636f6e74656e74002100000047726561742061727469636c6521205665727920696e666f726d61746976652e000974696d657374616d700080131c118901000000033100620000000275736572000c0000006361726f6c5f64617669730002636f6e74656e7400270000005468616e6b7320666f72206578706c61696e696e67207468697320736f20636c6561726c7921000974696d657374616d7000a0bd6011890100000000036d65746164617461003100000010766965777300e2040000106c696b6573002d0000000172656164696e675f74696d65000000000000002140000000"
            ),
            mode="extended_json",
        ) == {
            "post": {
                "id": {"$uuid": "2657d16c-0733-4f09-ae32-d778a21c062f"},
                "title": "Understanding BSON Encoding",
                "content": "BSON (Binary JSON) is a binary-encoded serialization of JSON-like documents...",
                "author": {
                    "id": {"$uuid": "3657d16c-0733-4f09-ae32-d778a21c0630"},
                    "name": "Alice Smith",
                    "email": "alice.smith@example.com",
                },
                "tags": ["programming", "database", "mongodb"],
                "created_at": {"$date": patch_utc_isoformat("2023-07-01T10:30:00.000Z")},
                "updated_at": {"$date": patch_utc_isoformat("2023-07-02T15:45:00.000Z")},
                "comments": [
                    {
                        "user": "bob_wilson",
                        "content": "Great article! Very informative.",
                        "timestamp": {"$date": patch_utc_isoformat("2023-07-01T11:00:00.000Z")},
                    },
                    {
                        "user": "carol_davis",
                        "content": "Thanks for explaining this so clearly!",
                        "timestamp": {"$date": patch_utc_isoformat("2023-07-01T12:15:00.000Z")},
                    },
                ],
                "metadata": {"views": 1250, "likes": 45, "reading_time": 8.5},
            }
        }
        assert lbson.decode(
            bytes.fromhex(
                "7d02000003706f737400720200000569640010000000042657d16c07334f09ae32d778a21c062f027469746c65001c000000556e6465727374616e64696e672042534f4e20456e636f64696e670002636f6e74656e74004f00000042534f4e202842696e617279204a534f4e2920697320612062696e6172792d656e636f6465642073657269616c697a6174696f6e206f66204a534f4e2d6c696b6520646f63756d656e74732e2e2e0003617574686f7200570000000569640010000000043657d16c07334f09ae32d778a21c0630026e616d65000c000000416c69636520536d6974680002656d61696c0018000000616c6963652e736d697468406578616d706c652e636f6d0000047461677300370000000230000c00000070726f6772616d6d696e670002310009000000646174616261736500023200080000006d6f6e676f6462000009637265617465645f617400409c00118901000009757064617465645f617400605c47178901000004636f6d6d656e747300c80000000330005b0000000275736572000b000000626f625f77696c736f6e0002636f6e74656e74002100000047726561742061727469636c6521205665727920696e666f726d61746976652e000974696d657374616d700080131c118901000000033100620000000275736572000c0000006361726f6c5f64617669730002636f6e74656e7400270000005468616e6b7320666f72206578706c61696e696e67207468697320736f20636c6561726c7921000974696d657374616d7000a0bd6011890100000000036d65746164617461003100000010766965777300e2040000106c696b6573002d0000000172656164696e675f74696d65000000000000002140000000"
            ),
            mode="python",
        ) == {
            "post": {
                "id": uuid.UUID("2657d16c-0733-4f09-ae32-d778a21c062f"),
                "title": "Understanding BSON Encoding",
                "content": "BSON (Binary JSON) is a binary-encoded serialization of JSON-like documents...",
                "author": {
                    "id": uuid.UUID("3657d16c-0733-4f09-ae32-d778a21c0630"),
                    "name": "Alice Smith",
                    "email": "alice.smith@example.com",
                },
                "tags": ["programming", "database", "mongodb"],
                "created_at": datetime.datetime(2023, 7, 1, 10, 30, tzinfo=datetime.timezone.utc),
                "updated_at": datetime.datetime(2023, 7, 2, 15, 45, tzinfo=datetime.timezone.utc),
                "comments": [
                    {
                        "user": "bob_wilson",
                        "content": "Great article! Very informative.",
                        "timestamp": datetime.datetime(2023, 7, 1, 11, 0, tzinfo=datetime.timezone.utc),
                    },
                    {
                        "user": "carol_davis",
                        "content": "Thanks for explaining this so clearly!",
                        "timestamp": datetime.datetime(2023, 7, 1, 12, 15, tzinfo=datetime.timezone.utc),
                    },
                ],
                "metadata": {"views": 1250, "likes": 45, "reading_time": 8.5},
            }
        }

    def test_decode_empty_name_field(self) -> None:
        assert lbson.decode(bytes.fromhex("070000000a0000")) == {"": None}
        assert lbson.decode(bytes.fromhex("0800000008000100")) == {"": True}
        assert lbson.decode(bytes.fromhex("0b00000010000100000000")) == {"": 1}
        assert lbson.decode(bytes.fromhex("0b0000001000ffffff7f00")) == {"": 2147483647}
        assert lbson.decode(bytes.fromhex("12000000020007000000737472696e670000")) == {"": "string"}


class TestDecodeOptions:
    def test_mode(self) -> None:
        with pytest.raises(ValueError, match="Invalid mode: invalid"):
            lbson.decode(
                bytes.fromhex("070000000a0000"),
                mode="invalid",  # type: ignore
            )

    def test_max_depth(self) -> None:
        assert lbson.decode(
            bytes.fromhex(
                "5c000000036100540000000362004c000000036300440000000364003c000000036500340000000366002c000000036700240000000368001c00000003690014000000036a000c000000106b00010000000000000000000000000000"
            ),
            max_depth=10,
        ) == {"a": {"b": {"c": {"d": {"e": {"f": {"g": {"h": {"i": {"j": {"k": 1}}}}}}}}}}}

        with pytest.raises(ValueError, match="Maximum recursion depth exceeded"):
            lbson.decode(
                bytes.fromhex(
                    "64000000036100540000000362004c000000036300440000000364003c000000036500340000000366002c000000036700240000000368001c00000003690014000000036a000c000000036b000c0000000c6c00010000000000000000000000000000"
                ),
                max_depth=10,
            )


class TestDecodeExceptions:
    def test_invalid_size_data_raises_error(self) -> None:
        with pytest.raises(ValueError, match="Object length mismatch"):
            lbson.decode(
                bytes.fromhex(
                    "5b000000036100540000000362004c000000036300440000000364003c000000036500340000000366002c000000036700240000000368001c00000003690014000000036a000c000000106b00010000000000000000000000000000"
                ),
            )

    def test_invalid_length_string_raises_error(self) -> None:
        with pytest.raises(ValueError, match="Buffer underrun"):
            lbson.decode(bytes.fromhex("1a0000000261000f00000048656c6c6f2c20576f726c64210000"))

    def test_missing_string_nul_terminator_raises_error(self) -> None:
        with pytest.raises(ValueError, match="String not null-terminated"):
            lbson.decode(bytes.fromhex("1a0000000261000e00000048656c6c6f2c20576f726c64210100"))

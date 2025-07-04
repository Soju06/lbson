import random
import re
import string
import uuid
from datetime import datetime, timezone

import lbson


def get_bson_compatible_datetime() -> datetime:
    """Get a datetime compatible with BSON (millisecond precision)."""
    dt = datetime.now(timezone.utc)
    return dt.replace(microsecond=(dt.microsecond // 1000) * 1000)


def generate_large_text(size: int = 10000) -> str:
    """Generate large text content."""
    return "".join(random.choices(string.ascii_letters + string.digits + " \n", k=size))


def generate_large_binary(size: int = 5000) -> bytes:
    """Generate large binary data."""
    return bytes(random.randint(0, 255) for _ in range(size))


class TestLargeDocumentRoundTrip:
    def test_large_user_profile_document(self) -> None:
        """Test large user profile document with deep nesting and many fields."""
        # Generate many interests (1000 items)
        interests = [f"interest_{i}" for i in range(1000)]

        # Generate many friends (500 items)
        friends = [
            {
                "id": str(uuid.uuid4()),
                "name": f"Friend {i}",
                "relationship": random.choice(["friend", "colleague", "family"]),
                "since": get_bson_compatible_datetime(),
                "mutual_friends": random.randint(0, 50),
                "contact_info": {
                    "email": f"friend{i}@example.com",
                    "phone": f"+1-555-{random.randint(1000, 9999)}",
                    "address": {
                        "street": f"{random.randint(1, 9999)} {random.choice(['Main', 'Oak', 'Pine'])} St",
                        "city": f"City{random.randint(1, 100)}",
                        "country": random.choice(["US", "CA", "UK", "AU"]),
                        "postal_code": f"{random.randint(10000, 99999)}",
                    },
                },
            }
            for i in range(500)
        ]

        # Generate many posts (200 items)
        posts = [
            {
                "id": str(uuid.uuid4()),
                "content": generate_large_text(500),
                "created_at": get_bson_compatible_datetime(),
                "likes": random.randint(0, 1000),
                "comments": [
                    {
                        "id": str(uuid.uuid4()),
                        "user": f"user_{j}",
                        "content": generate_large_text(100),
                        "timestamp": get_bson_compatible_datetime(),
                    }
                    for j in range(random.randint(0, 20))
                ],
                "media": [
                    {
                        "type": "image",
                        "url": f"https://example.com/image_{j}.jpg",
                        "thumbnail": generate_large_binary(500),
                        "size": random.randint(100000, 5000000),
                    }
                    for j in range(random.randint(0, 5))
                ],
                "hashtags": [f"#tag{j}" for j in range(random.randint(0, 10))],
                "location": {
                    "name": f"Location {i}",
                    "coordinates": {"lat": random.uniform(-90, 90), "lng": random.uniform(-180, 180)},
                    "accuracy": random.uniform(1, 100),
                },
            }
            for i in range(200)
        ]

        large_user_profile = {
            "user_id": str(uuid.uuid4()),
            "username": "large_user_profile_test",
            "profile": {
                "personal_info": {
                    "first_name": "John",
                    "last_name": "Doe",
                    "birth_date": datetime(1990, 1, 1, tzinfo=timezone.utc),
                    "bio": generate_large_text(5000),
                    "languages": [
                        {"code": "en", "name": "English", "proficiency": "native"},
                        {"code": "ko", "name": "Korean", "proficiency": "fluent"},
                        {"code": "ja", "name": "Japanese", "proficiency": "intermediate"},
                    ],
                },
                "contact_info": {
                    "email": "john.doe@example.com",
                    "phone": "+1-555-0123",
                    "social_media": {
                        "twitter": "@johndoe",
                        "instagram": "@johndoe_insta",
                        "linkedin": "johndoe",
                        "github": "johndoe_dev",
                    },
                    "addresses": [
                        {
                            "type": "home",
                            "street": "123 Main St",
                            "city": "New York",
                            "country": "US",
                            "postal_code": "10001",
                            "coordinates": {"lat": 40.7589, "lng": -73.9851},
                        },
                        {
                            "type": "work",
                            "street": "456 Business Ave",
                            "city": "San Francisco",
                            "country": "US",
                            "postal_code": "94105",
                            "coordinates": {"lat": 37.7749, "lng": -122.4194},
                        },
                    ],
                },
                "preferences": {
                    "privacy": {
                        "profile_visibility": "public",
                        "email_notifications": True,
                        "push_notifications": True,
                        "data_sharing": False,
                    },
                    "display": {
                        "theme": "dark",
                        "language": "en",
                        "timezone": "America/New_York",
                        "date_format": "YYYY-MM-DD",
                    },
                    "interests": interests,
                    "subscription_preferences": {
                        "newsletter": True,
                        "promotions": False,
                        "updates": True,
                    },
                },
                "statistics": {
                    "total_posts": len(posts),
                    "total_friends": len(friends),
                    "total_likes_received": sum(post["likes"] for post in posts),
                    "join_date": get_bson_compatible_datetime(),
                    "last_login": get_bson_compatible_datetime(),
                    "login_count": random.randint(1000, 10000),
                    "profile_views": random.randint(10000, 100000),
                },
            },
            "social": {
                "friends": friends,
                "posts": posts,
                "groups": [
                    {
                        "id": str(uuid.uuid4()),
                        "name": f"Group {i}",
                        "description": generate_large_text(200),
                        "member_count": random.randint(10, 1000),
                        "created_at": get_bson_compatible_datetime(),
                        "is_admin": random.choice([True, False]),
                    }
                    for i in range(50)
                ],
            },
            "settings": {
                "account": {
                    "two_factor_enabled": True,
                    "backup_email": "backup@example.com",
                    "security_questions": [
                        {"question": "What is your pet's name?", "answer_hash": "hash123"},
                        {"question": "What city were you born in?", "answer_hash": "hash456"},
                    ],
                },
                "notifications": {
                    "email": {"enabled": True, "frequency": "daily"},
                    "push": {"enabled": True, "quiet_hours": {"start": "22:00", "end": "08:00"}},
                    "sms": {"enabled": False, "number": None},
                },
            },
            "metadata": {
                "created_at": get_bson_compatible_datetime(),
                "updated_at": get_bson_compatible_datetime(),
                "version": "2.1.0",
                "data_checksum": "abc123def456",
                "backup_info": {
                    "last_backup": get_bson_compatible_datetime(),
                    "backup_size": random.randint(1000000, 10000000),
                    "backup_location": "s3://backups/user_profiles/",
                },
            },
        }

        # Round trip test
        encoded = lbson.encode(large_user_profile)
        decoded = lbson.decode(encoded)
        assert decoded == large_user_profile

        # Verify document size
        assert len(encoded) > 500000  # Should be over 500KB

    def test_large_log_data_document(self) -> None:
        """Test large log data document with massive arrays."""
        # Generate many log entries (10000 items)
        log_entries = [
            {
                "id": str(uuid.uuid4()),
                "timestamp": get_bson_compatible_datetime(),
                "level": random.choice(["DEBUG", "INFO", "WARN", "ERROR", "FATAL"]),
                "message": generate_large_text(200),
                "source": {
                    "service": f"service_{random.randint(1, 50)}",
                    "instance": f"instance_{random.randint(1, 100)}",
                    "version": f"v{random.randint(1, 10)}.{random.randint(0, 9)}.{random.randint(0, 9)}",
                    "environment": random.choice(["dev", "staging", "prod"]),
                },
                "request": {
                    "method": random.choice(["GET", "POST", "PUT", "DELETE", "PATCH"]),
                    "path": f"/api/v1/resource/{random.randint(1, 1000)}",
                    "query_params": {
                        "limit": random.randint(10, 100),
                        "offset": random.randint(0, 1000),
                        "sort": random.choice(["asc", "desc"]),
                    },
                    "headers": {
                        "user-agent": f"TestClient/1.0",
                        "content-type": "application/json",
                        "authorization": f"Bearer {uuid.uuid4()}",
                        "x-request-id": str(uuid.uuid4()),
                    },
                    "body_size": random.randint(0, 10000),
                },
                "response": {
                    "status_code": random.choice([200, 201, 400, 401, 403, 404, 500, 502, 503]),
                    "response_time_ms": random.randint(1, 5000),
                    "body_size": random.randint(0, 50000),
                    "headers": {
                        "content-type": "application/json",
                        "content-length": str(random.randint(0, 50000)),
                        "x-response-id": str(uuid.uuid4()),
                    },
                },
                "performance": {
                    "cpu_usage": random.uniform(0, 100),
                    "memory_usage": random.uniform(0, 100),
                    "network_io": random.randint(0, 1000000),
                    "disk_io": random.randint(0, 1000000),
                },
                "errors": (
                    [
                        {
                            "type": "ValidationError",
                            "message": generate_large_text(100),
                            "stack_trace": generate_large_text(500),
                            "line_number": random.randint(1, 1000),
                        }
                    ]
                    if random.random() < 0.1
                    else []
                ),
                "metrics": {
                    "database_queries": random.randint(0, 50),
                    "cache_hits": random.randint(0, 100),
                    "cache_misses": random.randint(0, 20),
                    "external_api_calls": random.randint(0, 10),
                },
                "user_context": {
                    "user_id": str(uuid.uuid4()) if random.random() < 0.8 else None,
                    "session_id": str(uuid.uuid4()),
                    "ip_address": f"{random.randint(1, 255)}.{random.randint(1, 255)}.{random.randint(1, 255)}.{random.randint(1, 255)}",
                    "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                    "geolocation": {
                        "country": random.choice(["US", "CA", "UK", "DE", "FR", "JP", "KR"]),
                        "city": f"City{random.randint(1, 100)}",
                        "coordinates": {"lat": random.uniform(-90, 90), "lng": random.uniform(-180, 180)},
                    },
                },
            }
            for i in range(10000)
        ]

        large_log_data = {
            "log_collection_id": str(uuid.uuid4()),
            "metadata": {
                "collection_start": get_bson_compatible_datetime(),
                "collection_end": get_bson_compatible_datetime(),
                "total_entries": len(log_entries),
                "services_monitored": 50,
                "instances_monitored": 100,
                "environments": ["dev", "staging", "prod"],
                "log_level_distribution": {
                    "DEBUG": sum(1 for entry in log_entries if entry["level"] == "DEBUG"),
                    "INFO": sum(1 for entry in log_entries if entry["level"] == "INFO"),
                    "WARN": sum(1 for entry in log_entries if entry["level"] == "WARN"),
                    "ERROR": sum(1 for entry in log_entries if entry["level"] == "ERROR"),
                    "FATAL": sum(1 for entry in log_entries if entry["level"] == "FATAL"),
                },
                "data_retention_policy": {
                    "retention_days": 90,
                    "archival_policy": "compress_and_store",
                    "deletion_policy": "auto_delete_after_retention",
                },
                "collection_settings": {
                    "sampling_rate": 1.0,
                    "batch_size": 1000,
                    "compression_enabled": True,
                    "encryption_enabled": True,
                },
            },
            "entries": log_entries,
            "aggregated_metrics": {
                "total_requests": len(log_entries),
                "avg_response_time": sum(entry["response"]["response_time_ms"] for entry in log_entries)
                / len(log_entries),
                "error_rate": sum(1 for entry in log_entries if entry["response"]["status_code"] >= 400)
                / len(log_entries),
                "top_endpoints": [
                    {"path": f"/api/v1/resource/{i}", "count": random.randint(10, 500)} for i in range(20)
                ],
                "top_errors": [{"error": f"Error type {i}", "count": random.randint(1, 100)} for i in range(10)],
                "performance_summary": {
                    "avg_cpu": sum(entry["performance"]["cpu_usage"] for entry in log_entries) / len(log_entries),
                    "avg_memory": sum(entry["performance"]["memory_usage"] for entry in log_entries) / len(log_entries),
                    "total_network_io": sum(entry["performance"]["network_io"] for entry in log_entries),
                    "total_disk_io": sum(entry["performance"]["disk_io"] for entry in log_entries),
                },
            },
            "analysis": {
                "alerts_triggered": [
                    {
                        "id": str(uuid.uuid4()),
                        "type": "HIGH_ERROR_RATE",
                        "severity": "critical",
                        "message": "Error rate exceeded 5% threshold",
                        "triggered_at": get_bson_compatible_datetime(),
                        "resolved_at": get_bson_compatible_datetime() if random.random() < 0.7 else None,
                        "affected_services": [f"service_{i}" for i in range(random.randint(1, 10))],
                    }
                    for _ in range(random.randint(0, 20))
                ],
                "anomalies_detected": [
                    {
                        "id": str(uuid.uuid4()),
                        "type": "RESPONSE_TIME_SPIKE",
                        "description": generate_large_text(200),
                        "detected_at": get_bson_compatible_datetime(),
                        "confidence": random.uniform(0.7, 1.0),
                        "affected_period": {
                            "start": get_bson_compatible_datetime(),
                            "end": get_bson_compatible_datetime(),
                        },
                    }
                    for _ in range(random.randint(0, 50))
                ],
                "insights": {
                    "peak_hours": [f"{i:02d}:00" for i in range(9, 18)],
                    "quietest_hours": [f"{i:02d}:00" for i in range(2, 6)],
                    "busiest_services": [f"service_{i}" for i in range(1, 6)],
                    "most_error_prone_endpoints": [f"/api/v1/resource/{i}" for i in range(1, 6)],
                },
            },
        }

        # Round trip test
        encoded = lbson.encode(large_log_data)
        decoded = lbson.decode(encoded)
        assert decoded == large_log_data

        # Verify document size
        assert len(encoded) > 2000000  # Should be over 2MB

    def test_deep_nested_structure(self) -> None:
        """Test deeply nested structure with many levels."""

        def create_nested_dict(depth: int, current_depth: int = 0) -> dict:
            """Create a nested dictionary with specified depth."""
            if current_depth >= depth:
                return {
                    "leaf_data": f"depth_{current_depth}",
                    "leaf_id": str(uuid.uuid4()),
                    "leaf_timestamp": get_bson_compatible_datetime(),
                    "leaf_values": [random.randint(1, 100) for _ in range(10)],
                }

            return {
                "level": current_depth,
                "level_id": str(uuid.uuid4()),
                "metadata": {
                    "created_at": get_bson_compatible_datetime(),
                    "type": f"level_{current_depth}",
                    "properties": {
                        "name": f"Level {current_depth}",
                        "description": f"This is nesting level {current_depth}",
                        "tags": [f"tag_{i}" for i in range(5)],
                    },
                },
                "children": [create_nested_dict(depth, current_depth + 1) for _ in range(2)],  # 2 children per level
                "sibling_data": {
                    "values": [random.uniform(0, 100) for _ in range(20)],
                    "mapping": {f"key_{i}": f"value_{i}" for i in range(50)},
                },
            }

        deep_nested_document = {
            "document_type": "deep_nested_structure",
            "max_depth": 10,
            "created_at": get_bson_compatible_datetime(),
            "root_structure": create_nested_dict(10),
            "metadata": {
                "structure_info": {
                    "total_levels": 50,
                    "branching_factor": 2,
                    "estimated_nodes": 2**50 - 1,  # 2^n - 1 for binary tree
                },
                "test_info": {
                    "test_name": "deep_nested_structure",
                    "purpose": "Test BSON encoding/decoding with deep nesting",
                    "created_by": "test_suite",
                },
            },
        }

        # Round trip test
        encoded = lbson.encode(deep_nested_document)
        decoded = lbson.decode(encoded)
        assert decoded == deep_nested_document

    def test_complex_list_structures(self) -> None:
        """Test complex list structures with various nesting patterns."""
        # Create matrix-like structure
        matrix_data = [[[random.randint(0, 100) for _ in range(20)] for _ in range(30)] for _ in range(40)]

        # Create jagged arrays
        jagged_arrays = [
            [
                {
                    "row_id": i,
                    "col_data": [
                        {
                            "value": random.uniform(0, 1000),
                            "metadata": {
                                "type": random.choice(["int", "float", "string"]),
                                "source": f"generator_{j}",
                                "timestamp": get_bson_compatible_datetime(),
                            },
                        }
                        for j in range(random.randint(5, 25))
                    ],
                }
                for i in range(random.randint(10, 50))
            ]
            for _ in range(20)
        ]

        # Create complex nested lists with mixed types
        mixed_nested_lists = [
            [
                random.randint(1, 100),
                random.uniform(0, 100),
                str(uuid.uuid4()),
                get_bson_compatible_datetime(),
                [
                    {
                        "nested_id": str(uuid.uuid4()),
                        "nested_value": random.choice([True, False, None]),
                        "nested_list": [random.choice([1, 2.5, "text", True, None]) for _ in range(10)],
                    }
                    for _ in range(5)
                ],
                {"dict_in_list": {"level1": {"level2": {"level3": [{"deep_value": i * j} for i in range(5)]}}}},
            ]
            for j in range(100)
        ]

        complex_list_document = {
            "document_type": "complex_list_structures",
            "created_at": get_bson_compatible_datetime(),
            "structures": {
                "matrix_data": matrix_data,
                "jagged_arrays": jagged_arrays,
                "mixed_nested_lists": mixed_nested_lists,
                "list_of_dicts": [
                    {
                        f"key_{i}_{j}": {
                            "value": random.randint(1, 1000),
                            "sub_list": [
                                {
                                    "sub_key": f"sub_value_{k}",
                                    "sub_timestamp": get_bson_compatible_datetime(),
                                }
                                for k in range(random.randint(1, 10))
                            ],
                        }
                        for j in range(random.randint(5, 15))
                    }
                    for i in range(50)
                ],
            },
            "statistics": {
                "total_matrix_elements": 40 * 30 * 20,
                "total_jagged_arrays": len(jagged_arrays),
                "total_mixed_lists": len(mixed_nested_lists),
            },
        }

        # Round trip test
        encoded = lbson.encode(complex_list_document)
        decoded = lbson.decode(encoded)
        assert decoded == complex_list_document

    def test_many_keys_document(self) -> None:
        """Test document with extremely many keys at various levels."""
        # Create document with many top-level keys
        many_keys_document = {
            "document_type": "many_keys_structure",
            "created_at": get_bson_compatible_datetime(),
        }

        # Add 10000 top-level keys
        for i in range(10000):
            many_keys_document[f"key_{i:05d}"] = {
                "value": random.randint(1, 1000),
                "type": random.choice(["A", "B", "C", "D", "E"]),
                "timestamp": get_bson_compatible_datetime(),
                "metadata": {f"meta_key_{j}": f"meta_value_{j}" for j in range(random.randint(1, 20))},
            }

        # Add a section with nested objects having many keys
        many_keys_document["nested_many_keys"] = {
            f"nested_section_{i}": {
                f"nested_key_{j}_{k}": {
                    "value": random.uniform(0, 1000),
                    "nested_metadata": {f"deep_key_{m}": random.choice([True, False, None]) for m in range(10)},
                }
                for j in range(100)
                for k in range(10)
            }
            for i in range(10)
        }

        # Round trip test
        encoded = lbson.encode(many_keys_document)
        decoded = lbson.decode(encoded)
        assert decoded == many_keys_document

    def test_mixed_complex_types(self) -> None:
        """Test document with complex mix of all BSON types."""
        mixed_document = {
            "document_type": "mixed_complex_types",
            "created_at": get_bson_compatible_datetime(),
            "type_showcase": {
                # String variations
                "strings": {
                    "short_strings": [f"str_{i}" for i in range(1000)],
                    "long_strings": [generate_large_text(100) for _ in range(100)],
                    "unicode_strings": [
                        "한글 텍스트",
                        "日本語テキスト",
                        "中文文本",
                        "🚀 Emoji text 🎉",
                        "Special chars: !@#$%^&*()_+-=[]{}|;:,.<>?",
                    ]
                    * 200,
                },
                # Number variations
                "numbers": {
                    "integers": [random.randint(-1000000, 1000000) for _ in range(5000)],
                    "floats": [random.uniform(-1000000, 1000000) for _ in range(5000)],
                    "large_integers": [random.randint(2**32, 2**60) for _ in range(1000)],
                    "small_floats": [random.uniform(0, 1) for _ in range(1000)],
                },
                # Boolean variations
                "booleans": {
                    "true_values": [True] * 1000,
                    "false_values": [False] * 1000,
                    "mixed_booleans": [random.choice([True, False]) for _ in range(2000)],
                },
                # Date/time variations
                "datetimes": {
                    "recent_dates": [get_bson_compatible_datetime() for _ in range(1000)],
                    "historical_dates": [
                        datetime(
                            random.randint(1900, 2000),
                            random.randint(1, 12),
                            random.randint(1, 28),
                            tzinfo=timezone.utc,
                        )
                        for _ in range(1000)
                    ],
                    "future_dates": [
                        datetime(
                            random.randint(2025, 2050),
                            random.randint(1, 12),
                            random.randint(1, 28),
                            tzinfo=timezone.utc,
                        )
                        for _ in range(1000)
                    ],
                },
                # UUID variations
                "uuids": {
                    "uuid_strings": [str(uuid.uuid4()) for _ in range(2000)],
                    "uuid_objects": [uuid.uuid4() for _ in range(2000)],
                },
                # Binary data variations
                "binaries": {
                    "small_binaries": [generate_large_binary(100) for _ in range(100)],
                    "medium_binaries": [generate_large_binary(1000) for _ in range(50)],
                    "large_binaries": [generate_large_binary(5000) for _ in range(20)],
                },
                # None/null values
                "nulls": {
                    "null_values": [None] * 1000,
                    "mixed_with_nulls": [
                        random.choice([None, "value", 42, True, get_bson_compatible_datetime()]) for _ in range(2000)
                    ],
                },
            },
            # Complex nested combinations
            "complex_combinations": [
                {
                    "combination_id": str(uuid.uuid4()),
                    "mixed_array": [
                        random.randint(1, 100),
                        random.uniform(0, 100),
                        str(uuid.uuid4()),
                        get_bson_compatible_datetime(),
                        random.choice([True, False, None]),
                        generate_large_binary(random.randint(100, 1000)),
                        {
                            "nested_dict": {
                                "deep_value": random.choice([1, 2.5, "text", True, None]),
                                "deep_list": [
                                    {
                                        "ultra_deep": {
                                            "value": i * j,
                                            "metadata": {
                                                "timestamp": get_bson_compatible_datetime(),
                                                "source": f"generator_{i}_{j}",
                                            },
                                        }
                                    }
                                    for i in range(3)
                                ],
                            }
                        },
                    ],
                    "type_matrix": {
                        f"type_{type_name}": [
                            {
                                "value": value,
                                "type_info": {
                                    "python_type": type(value).__name__,
                                    "is_none": value is None,
                                    "string_repr": str(value),
                                },
                            }
                            for value in [
                                42,
                                3.14,
                                "string",
                                True,
                                None,
                                get_bson_compatible_datetime(),
                                str(uuid.uuid4()),
                                generate_large_binary(100),
                            ]
                        ]
                        for type_name in ["int", "float", "str", "bool", "none", "datetime", "uuid", "bytes"]
                    },
                }
                for j in range(100)
            ],
        }

        # Round trip test
        encoded = lbson.encode(mixed_document)
        decoded = lbson.decode(encoded)
        assert decoded == mixed_document

    def test_recursive_pattern_structures(self) -> None:
        """Test structures that follow recursive patterns."""

        def create_tree_structure(depth: int, branching_factor: int = 3) -> dict:
            """Create a tree structure with specified depth and branching factor."""
            if depth <= 0:
                return {
                    "leaf": True,
                    "value": random.randint(1, 1000),
                    "data": [random.uniform(0, 100) for _ in range(10)],
                }

            return {
                "leaf": False,
                "depth": depth,
                "node_id": str(uuid.uuid4()),
                "node_data": {
                    "properties": {f"prop_{i}": random.randint(1, 100) for i in range(20)},
                    "metadata": {
                        "created_at": get_bson_compatible_datetime(),
                        "type": "internal_node",
                        "depth_info": {
                            "current_depth": depth,
                            "remaining_depth": depth - 1,
                        },
                    },
                },
                "children": [create_tree_structure(depth - 1, branching_factor) for _ in range(branching_factor)],
                "auxiliary_data": {
                    "values": [random.uniform(0, 1000) for _ in range(50)],
                    "connections": [str(uuid.uuid4()) for _ in range(10)],
                },
            }

        def create_graph_like_structure(num_nodes: int = 500) -> dict:
            """Create a graph-like structure with many interconnected nodes."""
            node_ids = [str(uuid.uuid4()) for _ in range(num_nodes)]

            nodes = {}
            for i, node_id in enumerate(node_ids):
                # Each node connects to random other nodes
                connections = random.sample(node_ids, random.randint(1, min(20, num_nodes)))
                nodes[node_id] = {
                    "index": i,
                    "connections": connections,
                    "node_data": {
                        "value": random.randint(1, 1000),
                        "properties": {f"prop_{j}": random.uniform(0, 100) for j in range(10)},
                        "metadata": {
                            "created_at": get_bson_compatible_datetime(),
                            "connection_count": len(connections),
                        },
                    },
                    "edge_data": {
                        connection_id: {
                            "weight": random.uniform(0, 1),
                            "type": random.choice(["strong", "weak", "neutral"]),
                            "properties": {
                                "created_at": get_bson_compatible_datetime(),
                                "last_updated": get_bson_compatible_datetime(),
                            },
                        }
                        for connection_id in connections
                    },
                }

            return nodes

        recursive_document = {
            "document_type": "recursive_pattern_structures",
            "created_at": get_bson_compatible_datetime(),
            "structures": {
                "binary_tree": create_tree_structure(10, 2),
                "ternary_tree": create_tree_structure(8, 3),
                "wide_tree": create_tree_structure(5, 10),
                "graph_structure": create_graph_like_structure(500),
                "nested_lists": [
                    [
                        [
                            {
                                "level": 3,
                                "data": [random.randint(1, 100) for _ in range(10)],
                                "nested_object": {
                                    "properties": {f"key_{k}": f"value_{k}" for k in range(20)},
                                    "timestamp": get_bson_compatible_datetime(),
                                },
                            }
                            for _ in range(5)
                        ]
                        for _ in range(10)
                    ]
                    for _ in range(20)
                ],
            },
            "pattern_metadata": {
                "tree_depths": [10, 8, 5],
                "branching_factors": [2, 3, 10],
                "graph_nodes": 500,
                "max_connections_per_node": 20,
            },
        }

        # Round trip test
        encoded = lbson.encode(recursive_document)
        decoded = lbson.decode(encoded)
        assert decoded == recursive_document

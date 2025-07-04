import re
import uuid
from datetime import datetime, timezone

import pytest

import lbson


def get_bson_compatible_datetime() -> datetime:
    """Get a datetime compatible with BSON (millisecond precision)."""
    dt = datetime.now(timezone.utc)
    return dt.replace(microsecond=(dt.microsecond // 1000) * 1000)


class TestRoundTrip:
    @pytest.mark.parametrize(
        "value",
        [
            # Case 1: E-commerce product data
            {
                "product_id": str(uuid.uuid4()),
                "name": "Smartphone Galaxy S24",
                "description": "Latest Android smartphone",
                "price": 1299.0,
                "category": "electronics",
                "tags": ["smartphone", "android", "5G"],
                "in_stock": True,
                "created_at": get_bson_compatible_datetime(),
                "updated_at": get_bson_compatible_datetime(),
                "variants": [
                    {"color": "black", "storage": "128GB", "price_diff": 0},
                    {"color": "white", "storage": "256GB", "price_diff": 200},
                ],
                "metadata": {
                    "weight": 168.0,
                    "dimensions": {"width": 70.6, "height": 146.3, "depth": 7.6},
                    "warranty_months": 24,
                },
                "image_data": b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01",
                "search_pattern": re.compile(r"galaxy|smartphone", re.IGNORECASE),
            },
            # Case 2: Order data
            {
                "order_id": str(uuid.uuid4()),
                "customer_id": str(uuid.uuid4()),
                "order_number": "ORD-2024-001234",
                "status": "processing",
                "created_at": get_bson_compatible_datetime(),
                "items": [
                    {
                        "product_id": str(uuid.uuid4()),
                        "name": "Wireless Earbuds",
                        "quantity": 2,
                        "unit_price": 199.0,
                        "total_price": 398.0,
                    },
                    {
                        "product_id": str(uuid.uuid4()),
                        "name": "Charging Cable",
                        "quantity": 1,
                        "unit_price": 29.0,
                        "total_price": 29.0,
                    },
                ],
                "shipping_address": {
                    "street": "123 Main St",
                    "city": "New York",
                    "postal_code": "10001",
                    "country": "US",
                    "coordinates": {"lat": 40.7589, "lng": -73.9851},
                },
                "payment": {
                    "method": "credit_card",
                    "amount": 427.0,
                    "currency": "USD",
                    "processed_at": get_bson_compatible_datetime(),
                    "transaction_id": str(uuid.uuid4()),
                },
                "receipt_data": b"PDF-1.4\n%\xe2\xe3\xcf\xd3\n",
                "tracking_regex": re.compile(r"^[A-Z]{2}\d{9}[A-Z]{2}$"),
            },
            # Case 3: IoT sensor data
            {
                "device_id": str(uuid.uuid4()),
                "device_type": "environmental_sensor",
                "location": "office_building_floor_3",
                "timestamp": get_bson_compatible_datetime(),
                "measurements": {
                    "temperature": 23.5,
                    "humidity": 65.2,
                    "air_quality_index": 42,
                    "noise_level": 35.8,
                    "light_intensity": 450.0,
                    "co2_ppm": 420,
                },
                "status": {
                    "online": True,
                    "battery_level": 87.5,
                    "signal_strength": -45,
                    "last_maintenance": get_bson_compatible_datetime(),
                    "firmware_version": "v2.1.4",
                },
                "alerts": [
                    {
                        "type": "warning",
                        "message": "Humidity level exceeds recommended range",
                        "triggered_at": get_bson_compatible_datetime(),
                        "resolved": False,
                    }
                ],
                "calibration_data": b"\x00\x01\x02\x03\x04\x05\x06\x07\x08\x09",
                "data_pattern": re.compile(r"temp:\d+\.\d+"),
                "geolocation": {"latitude": 40.7589, "longitude": -73.9851, "altitude": 85.0},
            },
            # Case 4: API log data
            {
                "log_id": str(uuid.uuid4()),
                "request_id": str(uuid.uuid4()),
                "timestamp": get_bson_compatible_datetime(),
                "method": "POST",
                "endpoint": "/api/v1/users",
                "status_code": 201,
                "response_time_ms": 245,
                "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
                "client_ip": "192.168.1.100",
                "request_headers": {
                    "content-type": "application/json",
                    "authorization": "Bearer token123",
                    "x-request-id": str(uuid.uuid4()),
                },
                "request_body": {
                    "name": "John Doe",
                    "email": "john.doe@example.com",
                    "age": 28,
                    "preferences": ["tech", "gaming", "music"],
                },
                "response_body": {
                    "id": str(uuid.uuid4()),
                    "name": "John Doe",
                    "created_at": get_bson_compatible_datetime(),
                },
                "error_details": None,
                "binary_payload": b"\x7b\x22\x6e\x61\x6d\x65\x22\x3a\x22\x74\x65\x73\x74\x22\x7d",
                "url_pattern": re.compile(r"^/api/v\d+/"),
            },
            # Case 5: Game player data
            {
                "player_id": str(uuid.uuid4()),
                "username": "DragonSlayer99",
                "level": 47,
                "experience": 125847,
                "last_login": get_bson_compatible_datetime(),
                "character": {
                    "class": "wizard",
                    "race": "elf",
                    "stats": {"strength": 15, "dexterity": 24, "intelligence": 31, "constitution": 18},
                    "equipment": [
                        {
                            "item_id": str(uuid.uuid4()),
                            "name": "Wizard's Staff",
                            "type": "weapon",
                            "rarity": "legendary",
                            "stats": {"magic_power": 85, "critical_chance": 12.5},
                        }
                    ],
                },
                "achievements": [
                    {
                        "id": str(uuid.uuid4()),
                        "name": "First Dungeon Clear",
                        "unlocked_at": get_bson_compatible_datetime(),
                        "points": 100,
                    }
                ],
                "save_data": b"\x00\x01\x47\x41\x4d\x45\x53\x41\x56\x45",
                "guild_regex": re.compile(r"^\[.+\].+"),
                "is_premium": True,
                "subscription_expires": get_bson_compatible_datetime(),
            },
            # Case 6: Medical patient data
            {
                "patient_id": str(uuid.uuid4()),
                "chart_number": "PT-2024-5678",
                "personal_info": {
                    "name": "Jane Smith",
                    "birth_date": datetime(1985, 3, 15, tzinfo=timezone.utc),
                    "gender": "female",
                    "blood_type": "A+",
                    "emergency_contact": {"name": "John Smith", "relationship": "spouse", "phone": "+1-555-123-4567"},
                },
                "visits": [
                    {
                        "visit_id": str(uuid.uuid4()),
                        "date": get_bson_compatible_datetime(),
                        "department": "Internal Medicine",
                        "doctor": "Dr. Johnson",
                        "diagnosis": ["Hypertension", "Diabetes"],
                        "prescriptions": [{"medication": "Metformin", "dosage": "500mg", "frequency": "Twice daily"}],
                        "vital_signs": {
                            "blood_pressure": {"systolic": 140, "diastolic": 90},
                            "heart_rate": 78,
                            "temperature": 98.6,
                            "weight": 143.7,
                        },
                    }
                ],
                "lab_results": {"blood_glucose": 126.0, "hba1c": 7.2, "cholesterol": 210.0},
                "medical_images": b"\xff\xd8\xff\xe0\x00\x10JFIF",
                "insurance_active": True,
                "mrn_pattern": re.compile(r"^PT-\d{4}-\d{4}$"),
            },
            # Case 7: Financial transaction data
            {
                "transaction_id": str(uuid.uuid4()),
                "account_id": str(uuid.uuid4()),
                "type": "transfer",
                "amount": 1500.0,
                "currency": "USD",
                "timestamp": get_bson_compatible_datetime(),
                "from_account": {"account_number": "123-456-789", "bank_code": "011", "holder_name": "John Customer"},
                "to_account": {"account_number": "987-654-321", "bank_code": "011", "holder_name": "Jane Recipient"},
                "status": "completed",
                "fee": 10.0,
                "description": "Monthly rent transfer",
                "risk_assessment": {
                    "score": 15.5,
                    "level": "low",
                    "factors": ["regular_pattern", "known_recipient"],
                    "checked_at": get_bson_compatible_datetime(),
                },
                "encrypted_data": b"\x01\x02\x03\x04\x05\x06\x07\x08",
                "memo_clean": True,
                "account_pattern": re.compile(r"^\d{3}-\d{3}-\d{3}$"),
                "exchange_rate": None,
            },
            # Case 8: Social media post data
            {
                "post_id": str(uuid.uuid4()),
                "user_id": str(uuid.uuid4()),
                "content": "Beautiful weather today! #lifestyle #weather",
                "created_at": get_bson_compatible_datetime(),
                "updated_at": get_bson_compatible_datetime(),
                "media": [
                    {
                        "media_id": str(uuid.uuid4()),
                        "type": "image",
                        "url": "https://cdn.example.com/images/12345.jpg",
                        "thumbnail": b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR",
                        "width": 1920,
                        "height": 1080,
                        "size_bytes": 245760,
                    }
                ],
                "engagement": {"likes": 42, "comments": 7, "shares": 3, "views": 256},
                "location": {"name": "Central Park", "latitude": 40.7829, "longitude": -73.9654, "accuracy": 5.0},
                "hashtags": ["lifestyle", "weather", "park"],
                "mentions": [str(uuid.uuid4())],
                "visibility": "public",
                "reported": False,
                "hashtag_pattern": re.compile(r"#\w+"),
                "analytics_data": b"\x7b\x22\x76\x69\x65\x77\x73\x22\x3a\x32\x35\x36\x7d",
            },
            # Case 9: Shipping tracking data
            {
                "tracking_id": str(uuid.uuid4()),
                "tracking_number": "US1234567890US",
                "order_id": str(uuid.uuid4()),
                "carrier": "FedEx",
                "created_at": get_bson_compatible_datetime(),
                "origin": {
                    "address": "123 Warehouse Blvd, Chicago IL",
                    "postal_code": "60601",
                    "coordinates": {"lat": 41.8781, "lng": -87.6298},
                    "facility_type": "warehouse",
                },
                "destination": {
                    "address": "456 Office St, New York NY",
                    "postal_code": "10001",
                    "coordinates": {"lat": 40.7589, "lng": -73.9851},
                    "facility_type": "office",
                },
                "package_info": {
                    "weight_kg": 2.5,
                    "dimensions": {"length": 30, "width": 20, "height": 15},
                    "value": 180.0,
                    "fragile": False,
                    "requires_signature": True,
                },
                "tracking_events": [
                    {
                        "event_id": str(uuid.uuid4()),
                        "timestamp": get_bson_compatible_datetime(),
                        "status": "picked_up",
                        "location": "Chicago Distribution Center",
                        "description": "Package has been picked up",
                    },
                    {
                        "event_id": str(uuid.uuid4()),
                        "timestamp": get_bson_compatible_datetime(),
                        "status": "in_transit",
                        "location": "New York Sorting Center",
                        "description": "Package is being processed at sorting center",
                    },
                ],
                "estimated_delivery": get_bson_compatible_datetime(),
                "barcode_data": b"\x00\x01\x02\x03\x04\x05",
                "tracking_pattern": re.compile(r"^[A-Z]{2}\d{10}[A-Z]{2}$"),
                "delivered": False,
            },
            # Case 10: Educational course data
            {
                "course_id": str(uuid.uuid4()),
                "course_code": "CS101",
                "title": "Introduction to Computer Science",
                "description": "Basic programming and computer science fundamentals",
                "instructor": {
                    "instructor_id": str(uuid.uuid4()),
                    "name": "Dr. Wilson",
                    "email": "prof.wilson@university.edu",
                    "department": "Computer Science",
                },
                "schedule": {
                    "semester": "2024-1",
                    "days": ["Monday", "Wednesday", "Friday"],
                    "time": "09:00-10:30",
                    "room": "Engineering Building 301",
                    "start_date": datetime(2024, 3, 4, tzinfo=timezone.utc),
                    "end_date": datetime(2024, 6, 21, tzinfo=timezone.utc),
                },
                "students": [
                    {
                        "student_id": str(uuid.uuid4()),
                        "name": "Alex Student",
                        "student_number": "2024001234",
                        "major": "Computer Engineering",
                        "enrollment_date": get_bson_compatible_datetime(),
                        "grades": {
                            "midterm": 85.5,
                            "final": 92.0,
                            "assignments": [88, 91, 76, 94],
                            "participation": 95.0,
                        },
                    }
                ],
                "curriculum": {
                    "modules": [
                        {"week": 1, "topic": "Programming Basics", "materials": ["lecture.pdf", "code.py"]},
                        {"week": 2, "topic": "Data Structures", "materials": ["slides.pptx"]},
                    ],
                    "assignments": 4,
                    "total_hours": 45,
                },
                "course_materials": b"PDF-1.4\n%\xe2\xe3\xcf\xd3",
                "active": True,
                "capacity": 50,
                "enrolled_count": 23,
                "grade_pattern": re.compile(r"^[A-F][+-]?$"),
                "evaluation_criteria": {"midterm": 30.0, "final": 40.0, "assignments": 20.0, "participation": 10.0},
            },
        ],
    )
    def test_round_trip(self, value: dict) -> None:
        decoded = value

        for _ in range(100):
            encoded = lbson.encode(decoded)
            decoded = lbson.decode(encoded)
            assert decoded == value

#pragma once

#include <stdint.h>

constexpr uint8_t BSON_NUL_TERM = 0;

enum class bson_type : int8_t {
    BSON_TYPE_DOUBLE = 0x01,
    BSON_TYPE_STRING = 0x02,
    BSON_TYPE_OBJECT = 0x03,
    BSON_TYPE_ARRAY = 0x04,
    BSON_TYPE_BINARY = 0x05,
    BSON_TYPE_UNDEFINED [[deprecated]] = 0x06,
    __BSON_TYPE_UNDEFINED = 0x06,  // ignore deprecated type
    BSON_TYPE_OBJECTID = 0x07,
    BSON_TYPE_BOOL = 0x08,
    BSON_TYPE_UTC_DATETIME = 0x09,
    BSON_TYPE_NULL = 0x0A,
    BSON_TYPE_REGEX = 0x0B,
    BSON_TYPE_DBPOINTER [[deprecated]] = 0x0C,
    __BSON_TYPE_DBPOINTER = 0x0C,  // ignore deprecated type
    BSON_TYPE_JAVASCRIPT = 0x0D,
    BSON_TYPE_SYMBOL [[deprecated]] = 0x0E,
    __BSON_TYPE_SYMBOL = 0x0E,  // ignore deprecated type
    BSON_TYPE_INT32 = 0x10,
    BSON_TYPE_TIMESTAMP = 0x11,
    BSON_TYPE_INT64 = 0x12,
    BSON_TYPE_DECIMAL128 = 0x13,
    BSON_TYPE_MINKEY = -1,
    BSON_TYPE_MAXKEY = 0x7F
};

enum class bson_subtype : uint8_t {
    BSON_SUB_GENERIC = 0x00,
    BSON_SUB_FUNCTION = 0x01,
    BSON_SUB_BINARY_OLD [[deprecated]] = 0x02,
    __BSON_SUB_BINARY_OLD = 0x02,  // ignore deprecated type
    BSON_SUB_UUID_OLD [[deprecated]] = 0x03,
    __BSON_SUB_UUID_OLD = 0x03,  // ignore deprecated type
    BSON_SUB_UUID = 0x04,
    BSON_SUB_MD5 = 0x05,
    BSON_SUB_ENCRYPTED = 0x06,
    BSON_SUB_COMPRESSED = 0x07,
    BSON_SUB_SENSITIVE = 0x08,
    BSON_SUB_VECTOR = 0x09,
    BSON_SUB_USER_MIN = 0x80
};

struct bson_objectid {
    uint8_t data[12];
};
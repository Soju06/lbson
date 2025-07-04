#pragma once

#include <stdint.h>

#include <type_traits>

#if (defined(_WIN16) || defined(_WIN32) || defined(_WIN64)) && !defined(__WINDOWS__)
#define __WINDOWS__
#endif

#if defined(__linux__) || defined(__CYGWIN__)
#include <endian.h>
#elif defined(__APPLE__)
#include <libkern/OSByteOrder.h>
#define htole16(x) OSSwapHostToLittleInt16(x)
#define htole32(x) OSSwapHostToLittleInt32(x)
#define htole64(x) OSSwapHostToLittleInt64(x)
#define le16toh(x) OSSwapLittleToHostInt16(x)
#define le32toh(x) OSSwapLittleToHostInt32(x)
#define le64toh(x) OSSwapLittleToHostInt64(x)
#elif defined(__OpenBSD__)
#include <sys/endian.h>
#elif defined(__NetBSD__) || defined(__FreeBSD__) || defined(__DragonFly__)
#include <sys/endian.h>
#define le16toh(x) letoh16(x)
#define le32toh(x) letoh32(x)
#define le64toh(x) letoh64(x)
#elif defined(__WINDOWS__)
#include <sys/param.h>
#include <winsock2.h>
#if BYTE_ORDER == LITTLE_ENDIAN
#define htole16(x) (x)
#define htole32(x) (x)
#define htole64(x) (x)
#define le16toh(x) (x)
#define le32toh(x) (x)
#define le64toh(x) (x)
#elif BYTE_ORDER == BIG_ENDIAN
#define htole16(x) __builtin_bswap16(x)
#define htole32(x) __builtin_bswap32(x)
#define htole64(x) __builtin_bswap64(x)
#define le16toh(x) __builtin_bswap16(x)
#define le32toh(x) __builtin_bswap32(x)
#define le64toh(x) __builtin_bswap64(x)
#else
#error byte order not supported
#endif
#else
#error platform not supported
#endif

template <typename T>
inline T to_little_endian(T value) {
    static_assert(std::is_integral<T>::value, "Only integral types supported");
    if constexpr (sizeof(T) == 1) {
        return value;
    } else if constexpr (sizeof(T) == 2) {
        return static_cast<T>(htole16(static_cast<uint16_t>(value)));
    } else if constexpr (sizeof(T) == 4) {
        return static_cast<T>(htole32(static_cast<uint32_t>(value)));
    } else if constexpr (sizeof(T) == 8) {
        return static_cast<T>(htole64(static_cast<uint64_t>(value)));
    } else {
        static_assert(sizeof(T) <= 8, "Unsupported type size");
    }
}

template <typename T>
inline T from_little_endian(T value) {
    static_assert(std::is_integral<T>::value, "Only integral types supported");
    if constexpr (sizeof(T) == 1) {
        return value;
    } else if constexpr (sizeof(T) == 2) {
        return static_cast<T>(le16toh(static_cast<uint16_t>(value)));
    } else if constexpr (sizeof(T) == 4) {
        return static_cast<T>(le32toh(static_cast<uint32_t>(value)));
    } else if constexpr (sizeof(T) == 8) {
        return static_cast<T>(le64toh(static_cast<uint64_t>(value)));
    } else {
        static_assert(sizeof(T) <= 8, "Unsupported type size");
    }
}

inline double to_little_endian_double(double value) {
    static_assert(sizeof(double) == 8, "Double must be 8 bytes");
    union {
        double d;
        uint64_t u;
    } converter;
    converter.d = value;
    converter.u = htole64(converter.u);
    return converter.d;
}

inline double from_little_endian_double(double value) {
    static_assert(sizeof(double) == 8, "Double must be 8 bytes");
    union {
        double d;
        uint64_t u;
    } converter;
    converter.d = value;
    converter.u = le64toh(converter.u);
    return converter.d;
}

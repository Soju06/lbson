#pragma once

#include <stdint.h>
#include <stdlib.h>
#ifdef __cplusplus
#include <cstring>
#endif

#ifdef __has_include
#if __has_include(<endian.h>)
#include <endian.h>
#elif __has_include(<machine/endian.h>)
#include <machine/endian.h>
#elif __has_include(<sys/param.h>)
#include <sys/param.h>
#elif __has_include(<sys/isadefs.h>)
#include <sys/isadefs.h>
#endif
#endif

#if !defined(__LITTLE_ENDIAN__) && !defined(__BIG_ENDIAN__)
#if (defined(__BYTE_ORDER__) && __BYTE_ORDER__ == __ORDER_BIG_ENDIAN__) ||                                             \
    (defined(__BYTE_ORDER) && __BYTE_ORDER == __BIG_ENDIAN) || (defined(_BYTE_ORDER) && _BYTE_ORDER == _BIG_ENDIAN) || \
    (defined(BYTE_ORDER) && BYTE_ORDER == BIG_ENDIAN) ||                                                               \
    (defined(__sun) && defined(__SVR4) && defined(_BIG_ENDIAN)) || defined(__ARMEB__) || defined(__THUMBEB__) ||       \
    defined(__AARCH64EB__) || defined(_MIBSEB) || defined(__MIBSEB) || defined(__MIBSEB__) || defined(_M_PPC)
#define __BIG_ENDIAN__
#elif (defined(__BYTE_ORDER__) && __BYTE_ORDER__ == __ORDER_LITTLE_ENDIAN__) ||                                        \
    (defined(__BYTE_ORDER) && __BYTE_ORDER == __LITTLE_ENDIAN) ||                                                      \
    (defined(_BYTE_ORDER) && _BYTE_ORDER == _LITTLE_ENDIAN) || (defined(BYTE_ORDER) && BYTE_ORDER == LITTLE_ENDIAN) || \
    (defined(__sun) && defined(__SVR4) && defined(_LITTLE_ENDIAN)) || defined(__ARMEL__) || defined(__THUMBEL__) ||    \
    defined(__AARCH64EL__) || defined(_MIPSEL) || defined(__MIPSEL) || defined(__MIPSEL__) || defined(_M_IX86) ||      \
    defined(_M_X64) || defined(_M_IA64) || defined(_M_ARM) || defined(_M_ARM64) || defined(_M_ARM64EC)
#define __LITTLE_ENDIAN__
#endif
#endif

#if !defined(__LITTLE_ENDIAN__) && !defined(__BIG_ENDIAN__)
#error "UNKNOWN Platform / endianness. Configure endianness checks for this platform or set explicitly."
#endif

#if defined(bswap16) || defined(bswap32) || defined(bswap64) || defined(bswapf) || defined(bswapd)
#error "unexpected define!"
#endif

#if defined(_MSC_VER)
#define bswap16(x) _byteswap_ushort((x))
#define bswap32(x) _byteswap_ulong((x))
#define bswap64(x) _byteswap_uint64((x))
#elif (__GNUC__ > 4) || (__GNUC__ == 4 && __GNUC_MINOR__ >= 8)
#define bswap16(x) __builtin_bswap16((x))
#define bswap32(x) __builtin_bswap32((x))
#define bswap64(x) __builtin_bswap64((x))
#elif defined(__has_builtin) && __has_builtin(__builtin_bswap64)
#define bswap16(x) __builtin_bswap16((x))
#define bswap32(x) __builtin_bswap32((x))
#define bswap64(x) __builtin_bswap64((x))
#else

static inline uint16_t bswap16(uint16_t x) { return (((x >> 8) & 0xffu) | ((x & 0xffu) << 8)); }
static inline uint32_t bswap32(uint32_t x) {
    return (((x & 0xff000000u) >> 24) | ((x & 0x00ff0000u) >> 8) | ((x & 0x0000ff00u) << 8) |
            ((x & 0x000000ffu) << 24));
}
static inline uint64_t bswap64(uint64_t x) {
    return (((x & 0xff00000000000000ull) >> 56) | ((x & 0x00ff000000000000ull) >> 40) |
            ((x & 0x0000ff0000000000ull) >> 24) | ((x & 0x000000ff00000000ull) >> 8) |
            ((x & 0x00000000ff000000ull) << 8) | ((x & 0x0000000000ff0000ull) << 24) |
            ((x & 0x000000000000ff00ull) << 40) | ((x & 0x00000000000000ffull) << 56));
}
#endif

static inline float bswapf(float f) {
#ifdef __cplusplus
    static_assert(sizeof(float) == sizeof(uint32_t), "Unexpected float format");
    /* Problem: de-referencing float pointer as uint32_t breaks strict-aliasing rules for C++ and C, even if it normally
     * works uint32_t val = bswap32(*(reinterpret_cast<const uint32_t *>(&f))); return *(reinterpret_cast<float
     * *>(&val));
     */

    uint32_t asInt;
    std::memcpy(&asInt, reinterpret_cast<const void *>(&f), sizeof(uint32_t));
    asInt = bswap32(asInt);
    std::memcpy(&f, reinterpret_cast<void *>(&asInt), sizeof(float));
    return f;
#else
    _Static_assert(sizeof(float) == sizeof(uint32_t), "Unexpected float format");

    union {
        uint32_t asInt;
        float asFloat;
    } conversion_union;
    conversion_union.asFloat = f;
    conversion_union.asInt = bswap32(conversion_union.asInt);
    return conversion_union.asFloat;
#endif
}

static inline double bswapd(double d) {
#ifdef __cplusplus
    static_assert(sizeof(double) == sizeof(uint64_t), "Unexpected double format");
    uint64_t asInt;
    std::memcpy(&asInt, reinterpret_cast<const void *>(&d), sizeof(uint64_t));
    asInt = bswap64(asInt);
    std::memcpy(&d, reinterpret_cast<void *>(&asInt), sizeof(double));
    return d;
#else
    _Static_assert(sizeof(double) == sizeof(uint64_t), "Unexpected double format");
    union {
        uint64_t asInt;
        double asDouble;
    } conversion_union;
    conversion_union.asDouble = d;
    conversion_union.asInt = bswap64(conversion_union.asInt);
    return conversion_union.asDouble;
#endif
}

#if defined(__LITTLE_ENDIAN__)
#define ntoh16(x) bswap16((x))
#define hton16(x) bswap16((x))
#define ntoh32(x) bswap32((x))
#define hton32(x) bswap32((x))
#define ntoh64(x) bswap64((x))
#define hton64(x) bswap64((x))
#define ntohf(x) bswapf((x))
#define htonf(x) bswapf((x))
#define ntohd(x) bswapd((x))
#define htond(x) bswapd((x))
#elif defined(__BIG_ENDIAN__)
#define ntoh16(x) (x)
#define hton16(x) (x)
#define ntoh32(x) (x)
#define hton32(x) (x)
#define ntoh64(x) (x)
#define hton64(x) (x)
#define ntohf(x) (x)
#define htonf(x) (x)
#define ntohd(x) (x)
#define htond(x) (x)
#else
#warning "UNKNOWN Platform / endianness; network / host byte swaps not defined."
#endif

template <typename T>
inline T to_little_endian(T value) {
    static_assert(std::is_integral<T>::value || std::is_floating_point<T>::value,
                  "Only integral and floating point types supported");

    if constexpr (sizeof(T) == 1) {
        return value;
    } else if constexpr (sizeof(T) == 2) {
#if defined(__LITTLE_ENDIAN__)
        return value;
#elif defined(__BIG_ENDIAN__)
        return static_cast<T>(bswap16(static_cast<uint16_t>(value)));
#else
#error "Unknown endianness"
#endif
    } else if constexpr (sizeof(T) == 4) {
#if defined(__LITTLE_ENDIAN__)
        return value;
#elif defined(__BIG_ENDIAN__)
        if constexpr (std::is_floating_point<T>::value) {
            return static_cast<T>(bswapf(static_cast<float>(value)));
        } else {
            return static_cast<T>(bswap32(static_cast<uint32_t>(value)));
        }
#else
#error "Unknown endianness"
#endif
    } else if constexpr (sizeof(T) == 8) {
#if defined(__LITTLE_ENDIAN__)
        return value;
#elif defined(__BIG_ENDIAN__)
        if constexpr (std::is_floating_point<T>::value) {
            return static_cast<T>(bswapd(static_cast<double>(value)));
        } else {
            return static_cast<T>(bswap64(static_cast<uint64_t>(value)));
        }
#else
#error "Unknown endianness"
#endif
    } else {
        static_assert(sizeof(T) <= 8, "Unsupported type size");
    }
}

template <typename T>
inline T from_little_endian(T value) {
    static_assert(std::is_integral<T>::value || std::is_floating_point<T>::value,
                  "Only integral and floating point types supported");

    if constexpr (sizeof(T) == 1) {
        return value;
    } else if constexpr (sizeof(T) == 2) {
#if defined(__LITTLE_ENDIAN__)
        return value;
#elif defined(__BIG_ENDIAN__)
        return static_cast<T>(bswap16(static_cast<uint16_t>(value)));
#else
#error "Unknown endianness"
#endif
    } else if constexpr (sizeof(T) == 4) {
#if defined(__LITTLE_ENDIAN__)
        return value;
#elif defined(__BIG_ENDIAN__)
        if constexpr (std::is_floating_point<T>::value) {
            return static_cast<T>(bswapf(static_cast<float>(value)));
        } else {
            return static_cast<T>(bswap32(static_cast<uint32_t>(value)));
        }
#else
#error "Unknown endianness"
#endif
    } else if constexpr (sizeof(T) == 8) {
#if defined(__LITTLE_ENDIAN__)
        return value;
#elif defined(__BIG_ENDIAN__)
        if constexpr (std::is_floating_point<T>::value) {
            return static_cast<T>(bswapd(static_cast<double>(value)));
        } else {
            return static_cast<T>(bswap64(static_cast<uint64_t>(value)));
        }
#else
#error "Unknown endianness"
#endif
    } else {
        static_assert(sizeof(T) <= 8, "Unsupported type size");
    }
}

#pragma once

#include <Python.h>
#include <datetime.h>

#include "portable_endian.hpp"

#if PY_VERSION_HEX < 0x030A0000
#define Py_IsNone(x) ((x) == Py_None)
#define Py_IsTrue(x) ((x) == Py_True)
#define Py_IsFalse(x) ((x) == Py_False)
#endif

extern PyDateTime_CAPI *g_PyDateTimeAPI;

struct py_obj_deleter {
    inline void operator()(PyObject *obj) { Py_XDECREF(obj); }
};

using py_obj_ptr = std::unique_ptr<PyObject, py_obj_deleter>;

inline size_t cstrnlen(const char *s, size_t max_len) {
    auto end = static_cast<const char *>(memchr(s, '\0', max_len));
    if (!end) return max_len;
    return static_cast<size_t>(end - s);
}

inline void integer_to_str(int64_t value, char *buffer, size_t *out_size) {
    int index = 0;
    bool sign = true;
    uint64_t abs_value;

    if (value == 0) {
        buffer[index++] = '0';
        *out_size = index;
        return;
    }

    if (value < 0) {
        sign = false;
        abs_value = 0ULL - (uint64_t)value;
    } else {
        abs_value = (uint64_t)value;
    }

    uint64_t digit;
    while (abs_value > 0) {
        digit = abs_value % 10ULL;
        buffer[index++] = (char)digit + '0';
        abs_value /= 10;
    }

    if (!sign) buffer[index++] = '-';

    int start = 0;
    int end = index - 1;

    while (start < end) {
        char temp = buffer[start];
        buffer[start++] = buffer[end];
        buffer[end--] = temp;
    }

    *out_size = index;
}

const char hex_chars[16] = {'0', '1', '2', '3', '4', '5', '6', '7', '8', '9', 'a', 'b', 'c', 'd', 'e', 'f'};

inline void hex_encode(const uint8_t *src, size_t len, char *dst) {
    for (size_t i = 0; i < len; ++i) {
        dst[i * 2] = hex_chars[src[i] >> 4];
        dst[i * 2 + 1] = hex_chars[src[i] & 0x0F];
    }
}

inline void format_uuid(const char *uuid, char buffer[36]) {
    auto *u = reinterpret_cast<const uint8_t *>(uuid);
    buffer[8] = '-';
    buffer[13] = '-';
    buffer[18] = '-';
    buffer[23] = '-';
    hex_encode(u, 4, buffer);
    hex_encode(u + 4, 2, buffer + 9);
    hex_encode(u + 6, 2, buffer + 14);
    hex_encode(u + 8, 2, buffer + 19);
    hex_encode(u + 10, 6, buffer + 24);
}

inline const char base64_table[65] = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/";

inline std::unique_ptr<char[]> base64_encode(const char *src, size_t len, size_t *out_len) {
    char *out = reinterpret_cast<char *>(malloc(len * 4 / 3 + 4));
    if (!out) throw std::runtime_error("Failed to allocate memory");

    const char *end = src + len;
    const char *in = src;
    char *pos = out;
    while (end - in >= 3) {
        *pos++ = base64_table[in[0] >> 2];
        *pos++ = base64_table[((in[0] & 0x03) << 4) | (in[1] >> 4)];
        *pos++ = base64_table[((in[1] & 0x0f) << 2) | (in[2] >> 6)];
        *pos++ = base64_table[in[2] & 0x3f];
        in += 3;
    }

    if (end - in) {
        *pos++ = base64_table[in[0] >> 2];
        if (end - in == 1) {
            *pos++ = base64_table[(in[0] & 0x03) << 4];
            *pos++ = '=';
        } else {
            *pos++ = base64_table[((in[0] & 0x03) << 4) | (in[1] >> 4)];
            *pos++ = base64_table[(in[1] & 0x0f) << 2];
        }
        *pos++ = '=';
    }

    if (out_len) *out_len = pos - out;
    return std::unique_ptr<char[]>(out);
}

inline int64_t days_from_civil(int y, int m, int d) {
    y -= m <= 2;
    const int era = (y >= 0 ? y : y - 399) / 400;
    const unsigned yoe = (unsigned)(y - era * 400);                          // 0‒399
    const unsigned doy = (153 * (m + (m > 2 ? -3 : 9)) + 2) / 5 + d - 1;     // 0‒365
    const unsigned doe = yoe * 365 + yoe / 4 - yoe / 100 + yoe / 400 + doy;  // 0‒146 096

    return (int64_t)era * 146097 + (int64_t)doe - 719468;
}

inline int64_t utc_to_epoch_millis(int year, int month, int day, int hour, int minute, int second, int microsecond) {
    const int64_t days = days_from_civil(year, month, day);
    const int64_t secs = days * 86400LL + hour * 3600LL + minute * 60LL + second;
    if (secs < INT64_MIN / 1000LL || secs > INT64_MAX / 1000LL) return INT64_MIN;
    return secs * 1000LL + microsecond / 1000;
}

inline void civil_from_days(int64_t z, int *year, int *month, int *day) {
    z += 719468;
    const int64_t era = (z >= 0 ? z : z - 146096) / 146097;
    const unsigned doe = (unsigned)(z - era * 146097);                           // [0, 146096]
    const unsigned yoe = (doe - doe / 1460 + doe / 36524 - doe / 146096) / 365;  // [0, 399]
    const int y = (int)(yoe) + (int)(era) * 400;
    const unsigned doy = doe - (365 * yoe + yoe / 4 - yoe / 100);  // [0, 365]
    const unsigned mp = (5 * doy + 2) / 153;                       // [0, 11]
    const unsigned d = doy - (153 * mp + 2) / 5 + 1;               // [1, 31]
    const unsigned m = mp + (mp < 10 ? 3 : -9);                    // [1, 12]

    *year = y + (m <= 2);
    *month = m;
    *day = d;
}

inline void epoch_millis_to_civil(int64_t epoch_millis, int *year, int *month, int *day, int *hour, int *minute,
                                  int *second, int *microsecond) {
    const int64_t MS_PER_SEC = 1000;
    const int64_t SEC_PER_DAY = 86400;

    int64_t ms = epoch_millis % MS_PER_SEC;
    if (ms < 0) {
        ms += MS_PER_SEC;
        epoch_millis -= MS_PER_SEC;
    }

    int64_t secs = epoch_millis / MS_PER_SEC;
    int64_t days = secs / SEC_PER_DAY;
    int64_t secs_in_day = secs % SEC_PER_DAY;

    if (secs_in_day < 0) {
        secs_in_day += SEC_PER_DAY;
        days -= 1;
    }

    civil_from_days(days, year, month, day);

    *hour = (int)(secs_in_day / 3600);
    *minute = (int)((secs_in_day % 3600) / 60);
    *second = (int)(secs_in_day % 60);
    *microsecond = (int)(ms * 1000);  // Convert milliseconds to microseconds
}

/* # of bytes for year, month, day, hour, minute, second, and usecond. */
inline void unpack_datetime_fast(const unsigned char *p, int *y, int *m, int *d, int *H, int *M, int *S, int *us) {
    *y = (p[0] << 8) | p[1];
    *m = p[2];
    *d = p[3];
    *H = p[4];
    *M = p[5];
    *S = p[6];
    *us = (p[7] << 16) | (p[8] << 8) | p[9];
}

inline int64_t utcoffset_in_us(PyObject *dt, PyObject *tzinfo) {
    auto method_name = PyUnicode_InternFromString("utcoffset");
    if (!method_name) return INT64_MIN;
    auto delta = PyObject_CallMethodOneArg(tzinfo, method_name, dt);
    Py_DECREF(method_name);
    if (!delta) return INT64_MIN;

    if (delta == Py_None) {
        Py_DECREF(delta);
        return 0;
    }

    int64_t days = (int64_t)PyDateTime_DELTA_GET_DAYS(delta);
    int64_t secs = (int64_t)PyDateTime_DELTA_GET_SECONDS(delta);
    int64_t us = (int64_t)PyDateTime_DELTA_GET_MICROSECONDS(delta);
    Py_DECREF(delta);
    return (days * 86400LL + secs) * 1000000LL + us;
}

inline void unix_ms_to_iso8601_tz(int64_t ms_since_epoch, int offset_minutes, char *buffer, size_t size) {
    const int64_t MS_PER_SEC = 1000;
    time_t sec = (time_t)(ms_since_epoch / MS_PER_SEC);
    int msec = (int)(ms_since_epoch % MS_PER_SEC);
    if (msec < 0) {
        msec += MS_PER_SEC;
        --sec;
    }

    sec += (time_t)offset_minutes * 60;

    struct tm tm_loc;
#if defined(WIN32) || defined(_WIN32) || defined(__WIN32__) || defined(__NT__)
    gmtime_s(&tm_loc, &sec);
#else
    gmtime_r(&sec, &tm_loc);
#endif

    size_t len = strftime(buffer, size, "%Y-%m-%dT%H:%M:%S", &tm_loc);

    if (len && len < size) {
        char sign = '+';
        int abs_min = offset_minutes;
        if (abs_min < 0) {
            sign = '-';
            abs_min = -abs_min;
        }

        if (!offset_minutes) {
#if PY_VERSION_HEX >= 0x030B0000  // Python 3.11+ supports 'Z' suffix in fromisoformat()
            snprintf(buffer + len, size - len, ".%03dZ", msec);
#else
            snprintf(buffer + len, size - len, ".%03d+00:00", msec);
#endif
        } else {
            int off_h = abs_min / 60;
            int off_m = abs_min % 60;
            snprintf(buffer + len, size - len, ".%03d%c%02d:%02d", msec, sign, off_h, off_m);
        }
    }
}

inline py_obj_ptr make_dict() {
    py_obj_ptr dict(PyDict_New());
    if (!dict) throw std::runtime_error("Failed to create dict object");
    return dict;
}

inline py_obj_ptr make_interned_string(const char *str) {
    auto str_obj = PyUnicode_InternFromString(str);
    if (!str_obj) throw std::runtime_error("Failed to create string object");
    return py_obj_ptr(str_obj);
}

inline py_obj_ptr make_interned_string(const char *str, size_t len) {
    auto str_obj = PyUnicode_FromStringAndSize(str, len);
    if (!str_obj) throw std::runtime_error("Failed to create string object");
    PyUnicode_InternInPlace(&str_obj);
    return py_obj_ptr(str_obj);
}

inline py_obj_ptr make_string(const char *str, size_t len) {
    auto str_obj = PyUnicode_FromStringAndSize(str, len);
    if (!str_obj) throw std::runtime_error("Failed to create string object");
    return py_obj_ptr(str_obj);
}

inline void dict_set_item(PyObject *dict, PyObject *key, PyObject *value) {
    if (PyDict_SetItem(dict, key, value) == -1) throw std::runtime_error("Failed to set item");
}

inline void dict_set_item(PyObject *dict, const char *key, PyObject *value) {
    auto key_obj = make_interned_string(key);
    dict_set_item(dict, key_obj.get(), value);
}

inline void dict_set_item(PyObject *dict, const char *key, size_t key_len, PyObject *value) {
    auto key_obj = make_interned_string(key, key_len);
    dict_set_item(dict, key_obj.get(), value);
}

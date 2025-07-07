#include "encoder.hpp"

#include <datetime.h>

#include <algorithm>
#include <cmath>
#include <unordered_set>

#include "re.hpp"
#include "uuid.hpp"

#undef PyDateTimeAPI
#define PyDateTimeAPI g_PyDateTimeAPI

/* String Writer */

int32_t bson_write_string_value(PyObject *obj, bson_encoder_state &state, size_t out_type_offset) {
    Py_ssize_t len;
    auto utf8_data = PyUnicode_AsUTF8AndSize(obj, &len);
    if (!utf8_data) throw py::value_error("Invalid UTF-8 string");
    auto len_value = static_cast<int32_t>(len) + 1;
    state.write_little_endian(len_value);
    state.write(utf8_data, len);
    state.write_nul_terminator();
    if (out_type_offset != SIZE_MAX) state.insert_byte(out_type_offset, bson_type::BSON_TYPE_STRING);
    return sizeof(int32_t) + len + 1;
}

/* Integer Writer */

int32_t bson_write_integer_value(PyObject *obj, bson_encoder_state &state, size_t out_type_offset) {
    int overflow;
    auto int64_value = PyLong_AsLongLongAndOverflow(obj, &overflow);
    if (int64_value == -1 && PyErr_Occurred()) throw py::value_error("Cannot convert value to int64");
    if (overflow)
        throw py::value_error("Value " + std::to_string(int64_value) + " is too large. BSON integers must be at most " +
                              std::to_string(std::numeric_limits<int64_t>::max()));

    if (int64_value > INT32_MAX || int64_value < INT32_MIN) {
        state.write_little_endian(int64_value);
        if (out_type_offset != SIZE_MAX) state.insert_byte(out_type_offset, bson_type::BSON_TYPE_INT64);
        return sizeof(int64_t);
    }

    state.write_little_endian(static_cast<int32_t>(int64_value));
    if (out_type_offset != SIZE_MAX) state.insert_byte(out_type_offset, bson_type::BSON_TYPE_INT32);
    return sizeof(int32_t);
}

/* Float Writer */

int32_t bson_write_float_value(PyObject *obj, bson_encoder_state &state, size_t out_type_offset) {
    double float_value = PyFloat_AsDouble(obj);

    if (!state.options.allow_nan) {
#define ERROR_MESSAGE "Out of range float values are not JSON compliant: "
        if (std::isnan(float_value)) throw py::value_error(ERROR_MESSAGE "nan");
        if (std::isinf(float_value))
            throw py::value_error(float_value > 0 ? ERROR_MESSAGE "inf" : ERROR_MESSAGE "-inf");
#undef ERROR_MESSAGE
    }

    double converted_value = to_little_endian(float_value);
    state.write(&converted_value, sizeof(double));
    if (out_type_offset != SIZE_MAX) state.insert_byte(out_type_offset, bson_type::BSON_TYPE_DOUBLE);
    return sizeof(double);
}

/* Boolean Writer */

int32_t bson_write_boolean_value(PyObject *obj, bson_encoder_state &state, size_t out_type_offset) {
    bool boolean_value = Py_IsTrue(obj);
    state.write(&boolean_value, 1);
    if (out_type_offset != SIZE_MAX) state.insert_byte(out_type_offset, bson_type::BSON_TYPE_BOOL);
    return 1;
}

/* Object Writer */

int bson_write_object_key(PyObject *obj, bson_encoder_state &state, size_t *out_size) {
    if (Py_IsNone(obj)) {
        char null_data[] = "null";
        state.write(null_data, sizeof(null_data) - 1);
        *out_size = sizeof(null_data) - 1;
        return 0;
    }
    auto obj_type = Py_TYPE(obj);
    if (obj_type == &PyUnicode_Type) {
        Py_ssize_t len;
        auto utf8_data = PyUnicode_AsUTF8AndSize(obj, &len);
        if (!utf8_data) throw py::value_error("Invalid UTF-8 string");

        if (cstrnlen(utf8_data, len) != len) throw py::value_error("Key names must not contain '\\0' characters");

        if (len) state.write(utf8_data, len);
        *out_size = len;
        return 0;
    }
    if (obj_type == &PyBool_Type) {
        if (Py_IsTrue(obj)) {
            char true_data[] = "true";
            state.write(true_data, sizeof(true_data) - 1);
            *out_size = sizeof(true_data) - 1;
            return 0;
        } else {
            char false_data[] = "false";
            state.write(false_data, sizeof(false_data) - 1);
            *out_size = sizeof(false_data) - 1;
            return 0;
        }
    }
    if (obj_type == &PyLong_Type) {
        int overflow;
        auto int64_value = PyLong_AsLongLongAndOverflow(obj, &overflow);
        if (int64_value == -1 && PyErr_Occurred()) throw py::value_error("Cannot convert value to int64");
        if (overflow)
            throw py::value_error("Value " + std::to_string(int64_value) +
                                  " is too large. BSON integers must be at most " +
                                  std::to_string(std::numeric_limits<int64_t>::max()));
        char num_str[20];
        size_t len;
        integer_to_str(int64_value, num_str, &len);
        state.write(num_str, len);
        *out_size = len;
        return 0;
    }
    if (obj_type == &PyFloat_Type) {
        char buf[16];
        int len = snprintf(buf, sizeof(buf), "%g", PyFloat_AsDouble(obj));
        if (len < 0 || len >= sizeof(buf)) throw py::value_error("Failed to convert float to string");
        state.write(buf, len);
        *out_size = len;
        return 0;
    }

    if (!state.options.skipkeys) throw py::type_error("Unsupported key type: " + std::string(obj_type->tp_name));

    return -1;
}

int32_t bson_write_object_item_value(PyObject *key, PyObject *value, bson_encoder_state &state) {
    auto type_offset = state.reserve<bson_type>();
    size_t key_size;
    if (bson_write_object_key(key, state, &key_size) == -1) {
        state.offset -= sizeof(bson_type);
        return 0;
    }
    state.write_nul_terminator();
    return sizeof(bson_type) + key_size + 1 + bson_write_value(value, state, type_offset);
}

int32_t bson_write_object_value(PyObject *obj, bson_encoder_state &state, size_t out_type_offset) {
    PyObject *key, *value;
    Py_ssize_t pos = 0;
    size_t size_offset = state.reserve<int32_t>();
    int32_t size = sizeof(int32_t) + 1;  // size + terminator
    state.enter(obj);

    if (state.options.sort_keys) {
        Py_ssize_t str_len;
        std::vector<std::tuple<std::string, PyObject *, PyObject *>> keys;
        keys.reserve(PyDict_Size(obj));

        while (PyDict_Next(obj, &pos, &key, &value)) {
            auto utf8_data = PyUnicode_AsUTF8AndSize(key, &str_len);
            if (!utf8_data) throw py::value_error("Invalid UTF-8 string");
            keys.emplace_back(std::string(utf8_data, str_len), key, value);
        }

        std::sort(keys.begin(), keys.end());  // O(N log N)

        for (const auto &[_, key_obj, value_obj] : keys) {
            size += bson_write_object_item_value(key_obj, value_obj, state);
        }
    } else {
        while (PyDict_Next(obj, &pos, &key, &value)) {
            size += bson_write_object_item_value(key, value, state);
        }
    }

    state.write_nul_terminator();
    if (out_type_offset != SIZE_MAX) state.insert_byte(out_type_offset, bson_type::BSON_TYPE_OBJECT);
    state.insert_little_endian(size_offset, size);
    state.exit(obj);
    return size;
}

/* Array Writer */

int32_t bson_write_array_item_value(Py_ssize_t index, PyObject *obj, bson_encoder_state &state) {
    size_t type_offset = state.reserve<bson_type>();
    char num_str[20];
    size_t len;
    integer_to_str(static_cast<int64_t>(index), num_str, &len);
    state.write(num_str, len);
    state.write_nul_terminator();
    return sizeof(bson_type) + len + 1 + bson_write_value(obj, state, type_offset);
}

int32_t bson_write_array_value(PyObject *obj, bson_encoder_state &state, size_t out_type_offset) {
    auto obj_type = Py_TYPE(obj);
    size_t size_offset = state.reserve<int32_t>();
    int32_t size = sizeof(int32_t) + 1;  // size + terminator
    state.enter(obj);

    if (obj_type == &PyList_Type) {
    _PY_LIST_TYPE:
        auto list_size = PyList_Size(obj);
        for (Py_ssize_t i = 0; i < list_size; i++) {
            auto item = PyList_GetItem(obj, i);
            if (!item) throw py::value_error("Failed to get item from list");
            size += bson_write_array_item_value(i, item, state);
        }
        goto _WRITE_ARRAY_END;
    }

    if (obj_type == &PyTuple_Type) {
    _PY_TUPLE_TYPE:
        auto tuple_size = PyTuple_Size(obj);
        for (Py_ssize_t i = 0; i < tuple_size; i++) {
            auto item = PyTuple_GetItem(obj, i);
            if (!item) throw py::value_error("Failed to get item from tuple");
            size += bson_write_array_item_value(i, item, state);
        }
        goto _WRITE_ARRAY_END;
    }

    // slow path
    if (PyList_Check(obj)) goto _PY_LIST_TYPE;
    if (PyTuple_Check(obj)) goto _PY_TUPLE_TYPE;

    // sequence protocol
    {
        auto sequence_size = PySequence_Size(obj);
        for (Py_ssize_t i = 0; i < sequence_size; i++) {
            py_obj_ptr item(PySequence_GetItem(obj, i));
            if (!item) throw py::value_error("Failed to get item from sequence");
            size += bson_write_array_item_value(i, item.get(), state);
        }
        goto _WRITE_ARRAY_END;
    }

_WRITE_ARRAY_END:
    state.write_nul_terminator();
    if (out_type_offset != SIZE_MAX) state.insert_byte(out_type_offset, bson_type::BSON_TYPE_ARRAY);
    state.insert_little_endian(size_offset, size);
    state.exit(obj);
    return size;
}

/* DateTime Writer */

int32_t bson_write_datetime_value(PyObject *obj, bson_encoder_state &state, size_t out_type_offset) {
    PyDateTime_DateTime *datetime_obj = reinterpret_cast<PyDateTime_DateTime *>(obj);

    int y, m, d, H, M, S, us;
    unpack_datetime_fast(((_PyDateTime_BaseDateTime *)obj)->data, &y, &m, &d, &H, &M, &S, &us);

    if (((PyDateTime_DateTime *)obj)->hastzinfo && ((PyDateTime_DateTime *)obj)->tzinfo != Py_None) {
        PyObject *tzinfo = ((PyDateTime_DateTime *)obj)->tzinfo;
        int64_t off_us = utcoffset_in_us(obj, tzinfo);
        if (off_us == INT64_MIN) throw py::value_error("Failed to get utcoffset");
        int64_t ms = utc_to_epoch_millis(y, m, d, H, M, S, us);
        if (ms == INT64_MIN) throw std::overflow_error("epoch out of range");

        ms -= off_us / 1000;
        state.write_little_endian(ms);
    } else {
        int64_t ms = utc_to_epoch_millis(y, m, d, H, M, S, us);
        if (ms == INT64_MIN) throw std::overflow_error("epoch out of range");
        state.write_little_endian(ms);
    }
    if (out_type_offset != SIZE_MAX) state.insert_byte(out_type_offset, bson_type::BSON_TYPE_UTC_DATETIME);
    return sizeof(int64_t);
}

/* Regex Writer */

int32_t bson_write_regex_value(PyObject *obj, bson_encoder_state &state, size_t out_type_offset) {
    int32_t size = 0;
    py_obj_ptr flags(PyObject_GetAttrString(obj, "flags"));
    if (!flags) throw std::runtime_error("Failed to get flags attribute");

    {
        py_obj_ptr pattern(PyObject_GetAttrString(obj, "pattern"));
        if (!pattern) throw std::runtime_error("Failed to get pattern attribute");

        Py_ssize_t pattern_len;
        auto pattern_str = PyUnicode_AsUTF8AndSize(pattern.get(), &pattern_len);
        if (!pattern_str) throw std::runtime_error("Failed to convert pattern to UTF-8");
        state.write(pattern_str, pattern_len);
        state.write_nul_terminator();
        size += pattern_len + 1;
    }

    char flags_str[5];
    size_t flags_len = PyRe_GetFlagString(PyLong_AsLong(flags.get()), flags_str, sizeof(flags_str));
    if (flags_len == 0) throw std::runtime_error("Failed to get flag string");
    state.write(flags_str, flags_len);
    state.write_nul_terminator();
    size += flags_len + 1;

    if (out_type_offset != SIZE_MAX) state.insert_byte(out_type_offset, bson_type::BSON_TYPE_REGEX);
    return size;
}

/* Binary Writer */

int32_t bson_write_binary_value(PyObject *obj, bson_encoder_state &state, size_t out_type_offset) {
    auto obj_type = Py_TYPE(obj);
    size_t size_offset = state.reserve<int32_t>();
    state.write_byte(bson_subtype::BSON_SUB_GENERIC);
    int32_t size;

    if (obj_type == &PyBytes_Type) {
    _PY_BYTES_TYPE:
        size = PyBytes_GET_SIZE(obj);
        state.write(PyBytes_AS_STRING(obj), size);
        goto _WRITE_BINARY_END;
    }

    if (obj_type == &PyByteArray_Type) {
    _PY_BYTEARRAY_TYPE:
        size = PyByteArray_GET_SIZE(obj);
        state.write(PyByteArray_AS_STRING(obj), size);
        goto _WRITE_BINARY_END;
    }

    if (obj_type == &PyMemoryView_Type) {
    _PY_MEMORYVIEW_TYPE:
        auto buffer = PyMemoryView_GET_BUFFER(obj);
        state.write(buffer->buf, buffer->len);
        size = buffer->len;
        goto _WRITE_BINARY_END;
    }

    // slow path
    if (PyBytes_Check(obj)) goto _PY_BYTES_TYPE;
    if (PyByteArray_Check(obj)) goto _PY_BYTEARRAY_TYPE;
    if (PyMemoryView_Check(obj)) goto _PY_MEMORYVIEW_TYPE;

_WRITE_BINARY_END:
    if (out_type_offset != SIZE_MAX) state.insert_byte(out_type_offset, bson_type::BSON_TYPE_BINARY);
    state.insert_little_endian(size_offset, size);
    return sizeof(int32_t) + sizeof(bson_subtype) + size;
}

/* UUID Writer */

int32_t bson_write_uuid_value(PyObject *obj, bson_encoder_state &state, size_t out_type_offset) {
    char uuid[16];
    state.write_little_endian(static_cast<int32_t>(sizeof(uuid)));
    state.write_byte(bson_subtype::BSON_SUB_UUID);
    if (PyUuid_AsUUID(obj, uuid) == -1) throw py::value_error("Failed to convert UUID to bytes");
    state.write(uuid, sizeof(uuid));
    if (out_type_offset != SIZE_MAX) state.insert_byte(out_type_offset, bson_type::BSON_TYPE_BINARY);
    return sizeof(int32_t) + sizeof(bson_subtype) + sizeof(uuid);
}

/* Encoder */

int32_t bson_write_value(PyObject *obj, bson_encoder_state &state, size_t out_type_offset) {
    if (Py_IsNone(obj)) {
        state.insert_byte(out_type_offset, bson_type::BSON_TYPE_NULL);
        return 0;
    }

    auto obj_type = Py_TYPE(obj);
    // fast path
    if (obj_type == &PyUnicode_Type) return bson_write_string_value(obj, state, out_type_offset);
    if (obj_type == &PyBool_Type) return bson_write_boolean_value(obj, state, out_type_offset);
    if (obj_type == &PyLong_Type) return bson_write_integer_value(obj, state, out_type_offset);
    if (obj_type == &PyFloat_Type) return bson_write_float_value(obj, state, out_type_offset);
    if (obj_type == &PyDict_Type) return bson_write_object_value(obj, state, out_type_offset);
    if (obj_type == &PyList_Type || obj_type == &PyTuple_Type)
        return bson_write_array_value(obj, state, out_type_offset);
    if (obj_type == &PyBytes_Type || obj_type == &PyByteArray_Type || obj_type == &PyMemoryView_Type)
        return bson_write_binary_value(obj, state, out_type_offset);
    if (PyDateTimeAPI && obj_type == PyDateTimeAPI->DateTimeType)
        return bson_write_datetime_value(obj, state, out_type_offset);
    if (PyUuid_Module && obj_type == PyUuid_UUIDType) return bson_write_uuid_value(obj, state, out_type_offset);
    if (PyRe_Module && obj_type == PyRe_PatternType) return bson_write_regex_value(obj, state, out_type_offset);
    // slow path
    if (PyUnicode_Check(obj)) return bson_write_string_value(obj, state, out_type_offset);
    if (PyBool_Check(obj)) return bson_write_boolean_value(obj, state, out_type_offset);
    if (PyLong_Check(obj)) return bson_write_integer_value(obj, state, out_type_offset);
    if (PyFloat_Check(obj)) return bson_write_float_value(obj, state, out_type_offset);
    if (PyDict_Check(obj)) return bson_write_object_value(obj, state, out_type_offset);
    if (PyList_Check(obj) || PyTuple_Check(obj)) return bson_write_array_value(obj, state, out_type_offset);
    if (PyBytes_Check(obj) || PyByteArray_Check(obj) || PyMemoryView_Check(obj))
        return bson_write_binary_value(obj, state, out_type_offset);
    if (PyDateTimeAPI && PyDateTime_Check(obj)) return bson_write_datetime_value(obj, state, out_type_offset);
    if (PyUuid_Module && PyUUID_Check(obj)) return bson_write_uuid_value(obj, state, out_type_offset);
    if (PyRe_Module && PyPattern_Check(obj)) return bson_write_regex_value(obj, state, out_type_offset);
    // very slow path
    if (PySequence_Check(obj)) return bson_write_array_value(obj, state, out_type_offset);

    throw py::type_error("Unsupported type: " + std::string(obj_type->tp_name));
}

static thread_local std::unique_ptr<bson_encoder_state> tls_state;

bson_encoder_state &acquire_state(const bson_encoder_options &opt, size_t max_size) {
    if (tls_state && tls_state->max_size() != max_size) tls_state.reset();
    if (!tls_state)
        tls_state = std::make_unique<bson_encoder_state>(opt, INITIAL_BUFFER_SIZE, max_size);
    else {
        tls_state->options = opt;
        tls_state->clear();
    }
    return *tls_state;
}

py::bytes encode(const py::object &obj, const py::bool_ &skipkeys, const py::bool_ &check_circular,
                 const py::bool_ &allow_nan, const py::bool_ &sort_keys, const py::int_ &max_depth,
                 const py::int_ &max_size) {
    PyObject *obj_ptr = obj.ptr();
    bson_encoder_options options = {
        .skipkeys = skipkeys,
        .sort_keys = sort_keys,
        .allow_nan = allow_nan,
        .check_circular = check_circular,
        .max_depth = max_depth,
    };
    auto &state = acquire_state(options, max_size.cast<size_t>());

    auto written_size = bson_write_object_value(obj_ptr, state, SIZE_MAX);
    auto actual_size = state.size();

    if (written_size != actual_size)
        throw py::value_error("BSON size mismatch: " + std::to_string(written_size) +
                              " != " + std::to_string(actual_size));

    auto bytes = PyBytes_FromStringAndSize(reinterpret_cast<const char *>(state.buffer()), actual_size);

    tls_state->clear();

    if (!bytes) throw std::runtime_error("Failed to create bytes object");

    return py::reinterpret_steal<py::bytes>(bytes);
}

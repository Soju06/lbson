#include "decoder.hpp"

#include <datetime.h>

#include <algorithm>
#include <unordered_set>

#include "re.hpp"
#include "utils.hpp"
#include "uuid.hpp"

#undef PyDateTimeAPI
#define PyDateTimeAPI g_PyDateTimeAPI

/* String Reader */

int32_t bson_read_string_value(bson_decoder_state &state, PyObject **out_obj) {
    int32_t str_len;
    state.read_little_endian(&str_len);
    if (str_len < 1) throw py::value_error(state.make_error_msg("Invalid string length", std::to_string(str_len)));

    auto str_ptr = reinterpret_cast<const char *>(state.read(str_len));

    if (str_ptr[str_len - 1] != '\0')
        throw py::value_error(state.make_error_msg("String not null-terminated", "string extends to end of buffer"));

    *out_obj = PyUnicode_FromStringAndSize(str_ptr, str_len - 1);
    if (!*out_obj) throw std::runtime_error("Failed to create string object");
    return sizeof(int32_t) + str_len;
}

/* Integer Reader */

int32_t bson_read_int32_value(bson_decoder_state &state, PyObject **out_obj) {
    int32_t int_value;
    state.read_little_endian(&int_value);
    *out_obj = PyLong_FromLong(int_value);
    if (!*out_obj) throw std::runtime_error("Failed to create integer object");
    return sizeof(int32_t);
}

int32_t bson_read_int64_value(bson_decoder_state &state, PyObject **out_obj) {
    int64_t int_value;
    state.read_little_endian(&int_value);
    *out_obj = PyLong_FromLongLong(int_value);
    if (!*out_obj) throw std::runtime_error("Failed to create integer object");
    return sizeof(int64_t);
}

/* Float Reader */

int32_t bson_read_float_value(bson_decoder_state &state, PyObject **out_obj) {
    double converted_value = from_little_endian(*state.read<double>());
    *out_obj = PyFloat_FromDouble(converted_value);
    if (!*out_obj) throw std::runtime_error("Failed to create float object");
    return sizeof(double);
}

/* Boolean Reader */

int32_t bson_read_boolean_value(bson_decoder_state &state, PyObject **out_obj) {
    *out_obj = *state.read<uint8_t>() ? Py_True : Py_False;
    Py_INCREF(*out_obj);
    return 1;
}

/* Object Reader */

int32_t bson_read_object_value(bson_decoder_state &state, PyObject **out_obj) {
    int32_t obj_len;
    int32_t read_len = sizeof(int32_t) + 1;  // size + nul terminator

    state.enter();
    state.read_little_endian(&obj_len);
    if (obj_len < 0) throw py::value_error(state.make_error_msg("Invalid object length", std::to_string(obj_len)));

    auto obj = make_dict();
    auto obj_ptr = obj.get();

    bson_type type;
    const char *key;
    size_t key_len;
    PyObject *value;

    while (static_cast<uint8_t>(type = *state.read<bson_type>())) {
        state.read_string(&key, &key_len);
        auto key_obj = make_interned_string(key);

        // type + key + nul terminator + value
        read_len += sizeof(bson_type) + key_len + 1 + bson_read_value(type, state, &value);

        if (PyDict_SetItem(obj_ptr, key_obj.get(), value) == -1) {
            Py_DECREF(value);
            throw std::runtime_error("Failed to set item");
        }

        Py_DECREF(value);
    }

    if (read_len != obj_len)
        throw py::value_error(
            state.make_error_msg("Object length mismatch",
                                 "expected " + std::to_string(obj_len) + " bytes, read " + std::to_string(read_len)));

    state.exit();
    *out_obj = obj.release();
    return obj_len;
}

/* Array Reader */

int32_t bson_read_array_value(bson_decoder_state &state, PyObject **out_obj) {
    int32_t obj_len;
    int32_t read_len = sizeof(int32_t) + 1;  // size + nul terminator

    state.enter();
    state.read_little_endian(&obj_len);
    if (obj_len < 0) throw py::value_error(state.make_error_msg("Invalid array length", std::to_string(obj_len)));

    py_obj_ptr obj(PyList_New(0));
    if (!obj) throw std::runtime_error("Failed to create list object");
    auto obj_ptr = obj.get();

    bson_type type;
    const char *key;
    size_t key_len;
    PyObject *value;

    while (static_cast<uint8_t>(type = *state.read<bson_type>())) {
        state.read_string(&key, &key_len);
        // type + key + nul terminator + value
        read_len += sizeof(bson_type) + key_len + 1 + bson_read_value(type, state, &value);

        if (PyList_Append(obj_ptr, value) == -1) {
            Py_DECREF(value);
            throw std::runtime_error("Failed to set item");
        }

        Py_DECREF(value);
    }

    if (read_len != obj_len)
        throw py::value_error(
            state.make_error_msg("Array length mismatch",
                                 "expected " + std::to_string(obj_len) + " bytes, read " + std::to_string(read_len)));

    state.exit();
    *out_obj = obj.release();
    return obj_len;
}

/* DateTime Reader */

int32_t bson_read_datetime_value(bson_decoder_state &state, PyObject **out_obj) {
    int64_t milliseconds;
    state.read_little_endian(&milliseconds);
    PyObject *datetime_obj = nullptr;
    switch (state.options.mode) {
        case bson_decoder_mode::JSON: {
            char buffer[32];
            unix_ms_to_iso8601_tz(milliseconds, 0, buffer, sizeof(buffer));
            datetime_obj = PyUnicode_FromStringAndSize(buffer, cstrnlen(buffer, sizeof(buffer)));
            break;
        }
        case bson_decoder_mode::EXTENDED_JSON: {
            auto dict = make_dict();
            char buffer[32];
            unix_ms_to_iso8601_tz(milliseconds, 0, buffer, sizeof(buffer));
            auto date_str = make_string(buffer, cstrnlen(buffer, sizeof(buffer)));
            dict_set_item(dict.get(), "$date", date_str.get());
            datetime_obj = dict.release();
            break;
        }
        case bson_decoder_mode::PYTHON: {
            double timestamp = static_cast<double>(milliseconds) / 1000.0;
            py_obj_ptr tz_utc(PyDateTime_TimeZone_UTC);
            if (!tz_utc) throw std::runtime_error("Failed to get timezone object");
            Py_INCREF(tz_utc.get());

#if defined(WIN32) || defined(_WIN32) || defined(__WIN32__) || defined(__NT__)
            // Windows CPython doesn't support negative Unix timestamps, so we need to handle them specially
            if (timestamp < 0) {
                int year, month, day, hour, minute, second, microsecond;
                epoch_millis_to_civil(milliseconds, &year, &month, &day, &hour, &minute, &second, &microsecond);

                py_obj_ptr naive_dt(PyDateTime_FromDateAndTime(year, month, day, hour, minute, second, microsecond));
                if (!naive_dt) throw std::runtime_error("Failed to create datetime object");

                py_obj_ptr replace_method(PyObject_GetAttrString(naive_dt.get(), "replace"));
                if (!replace_method) throw std::runtime_error("Failed to get replace method");

                // Create keyword arguments for replace(tzinfo=tz_utc)
                py_obj_ptr kwnames(PyTuple_New(1));
                if (!kwnames) throw std::runtime_error("Failed to create kwnames tuple");

                auto tzinfo_name = PyUnicode_InternFromString("tzinfo");
                if (!tzinfo_name) throw std::runtime_error("Failed to create tzinfo string");
                PyTuple_SET_ITEM(kwnames.get(), 0, tzinfo_name);  // steals reference

                PyObject *args[] = {tz_utc.get()};
                datetime_obj = PyObject_Vectorcall(replace_method.get(), args, 0, kwnames.get());
                break;
            } else {
#endif
                py_obj_ptr timestamp_obj(PyFloat_FromDouble(timestamp));
                if (!timestamp_obj) throw std::runtime_error("Failed to create float object");
                py_obj_ptr args(Py_BuildValue("(OO)", timestamp_obj.get(), tz_utc.get()));
                datetime_obj = PyDateTime_FromTimestamp(args.get());
                break;
#if defined(WIN32) || defined(_WIN32) || defined(__WIN32__) || defined(__NT__)
            }
#endif
        }
        default:
            throw py::value_error(state.make_error_msg("Unsupported decode mode for datetime",
                                                       std::to_string(static_cast<uint8_t>(state.options.mode))));
    }
    if (!datetime_obj) throw std::runtime_error("Failed to create datetime object");
    *out_obj = datetime_obj;
    return sizeof(int64_t);
}

/* ObjectId Reader */

int32_t bson_read_objectid_value(bson_decoder_state &state, PyObject **out_obj) {
    // { "$oid": "66F8B200A1B2C3D4E5F60711" }
    auto objectid = *state.read<bson_objectid>();
    char hex_str[sizeof(objectid.data) * 2];
    hex_encode(objectid.data, sizeof(objectid.data), hex_str);
    auto objectid_obj = make_string(hex_str, sizeof(hex_str));

    switch (state.options.mode) {
        case bson_decoder_mode::JSON:
        case bson_decoder_mode::PYTHON:
            *out_obj = objectid_obj.release();
            break;
        case bson_decoder_mode::EXTENDED_JSON: {
            auto dict = make_dict();
            dict_set_item(dict.get(), "$oid", objectid_obj.get());
            *out_obj = dict.release();
            break;
        }
        default:
            throw py::value_error(state.make_error_msg("Unsupported decode mode for objectid",
                                                       std::to_string(static_cast<uint8_t>(state.options.mode))));
    }

    return sizeof(bson_objectid);
}

/* Regex Reader */

int32_t bson_read_regex_value(bson_decoder_state &state, PyObject **out_obj) {
    const char *pattern;
    size_t pattern_len;
    state.read_string(&pattern, &pattern_len);
    const char *flags;
    size_t flags_len;
    state.read_string(&flags, &flags_len);

    switch (state.options.mode) {
        case bson_decoder_mode::JSON: {
            auto regex_obj = PyUnicode_FromFormat("/%s/%s", pattern, flags);  // verified nul terminator
            if (!regex_obj) throw std::runtime_error("Failed to create regex object");
            *out_obj = regex_obj;
            break;
        }
        case bson_decoder_mode::EXTENDED_JSON: {
            auto dict = make_dict();
            auto regex_dict = make_dict();
            // { "$regularExpression": { "pattern": "...", "options": "..." } }
            auto pattern_str = make_string(pattern, pattern_len);
            auto options_str = make_string(flags, flags_len);
            dict_set_item(regex_dict.get(), "pattern", pattern_str.get());
            dict_set_item(regex_dict.get(), "options", options_str.get());
            dict_set_item(dict.get(), "$regularExpression", regex_dict.get());
            *out_obj = dict.release();
            break;
        }
        case bson_decoder_mode::PYTHON: {
            py_obj_ptr re_obj(PyRe_Compile(pattern, pattern_len, flags, flags_len));
            if (!re_obj) throw std::runtime_error("Failed to compile regex");
            *out_obj = re_obj.release();
            break;
        }
        default:
            throw py::value_error(state.make_error_msg("Unsupported decode mode for regex",
                                                       std::to_string(static_cast<uint8_t>(state.options.mode))));
    }

    return pattern_len + 1 + flags_len + 1;
}

/* Binary Reader */

int32_t bson_read_binary_value(bson_decoder_state &state, PyObject **out_obj) {
    int32_t size;
    state.read_little_endian(&size);
    if (size < 0) throw py::value_error(state.make_error_msg("Invalid binary size", std::to_string(size)));
    auto subtype = *state.read<bson_subtype>();

    switch (subtype) {
        case bson_subtype::BSON_SUB_UUID:
            bson_read_uuid_value(state, out_obj);
            break;
        case bson_subtype::BSON_SUB_GENERIC:
        case bson_subtype::BSON_SUB_SENSITIVE:
            bson_read_generic_binary_value(subtype, size, state, out_obj);
            break;
        // deprecated types
        case bson_subtype::__BSON_SUB_BINARY_OLD:
        case bson_subtype::__BSON_SUB_UUID_OLD:
        // unsupported types
        case bson_subtype::BSON_SUB_FUNCTION:
        case bson_subtype::BSON_SUB_MD5:
        case bson_subtype::BSON_SUB_ENCRYPTED:
        case bson_subtype::BSON_SUB_COMPRESSED:
        case bson_subtype::BSON_SUB_VECTOR:
        case bson_subtype::BSON_SUB_USER_MIN:
            *out_obj = Py_None;
            Py_INCREF(Py_None);
            break;
        default:
            throw py::value_error(
                state.make_error_msg("Unsupported binary subtype", std::to_string(static_cast<uint8_t>(subtype))));
    }

    return sizeof(int32_t) + sizeof(bson_subtype) + size;
}

void bson_read_generic_binary_value(bson_subtype subtype, int32_t size, bson_decoder_state &state, PyObject **out_obj) {
    switch (state.options.mode) {
        case bson_decoder_mode::JSON: {
            auto buffer = state.read(size);
            size_t base64_len;
            auto base64_str = base64_encode(reinterpret_cast<const char *>(buffer), size, &base64_len);
            auto base64_obj = PyUnicode_FromStringAndSize(base64_str.get(), base64_len);
            if (!base64_obj) throw std::runtime_error("Failed to create string object");
            *out_obj = base64_obj;
            break;
        }
        case bson_decoder_mode::EXTENDED_JSON: {
            auto dict = make_dict();
            auto base64_dict = make_dict();
            auto buffer = state.read(size);
            size_t base64_len;
            auto base64_str = base64_encode(reinterpret_cast<const char *>(buffer), size, &base64_len);
            py_obj_ptr base64_obj(PyUnicode_FromStringAndSize(base64_str.get(), base64_len));
            if (!base64_obj) throw std::runtime_error("Failed to create string object");
            auto sub_type_str = make_string(subtype == bson_subtype::BSON_SUB_SENSITIVE ? "08" : "00", 2);
            dict_set_item(base64_dict.get(), "base64", base64_obj.get());
            dict_set_item(base64_dict.get(), "subType", sub_type_str.get());
            dict_set_item(dict.get(), "$binary", base64_dict.get());
            *out_obj = dict.release();
            break;
        }
        case bson_decoder_mode::PYTHON: {
            auto buffer = state.read(size);
            auto obj = PyBytes_FromStringAndSize(reinterpret_cast<const char *>(buffer), size);
            if (!obj) throw std::runtime_error("Failed to create bytes object");
            *out_obj = obj;
            break;
        }
        default:
            throw py::value_error(state.make_error_msg("Unsupported decode mode for binary",
                                                       std::to_string(static_cast<uint8_t>(state.options.mode))));
    }
}

void bson_read_uuid_value(bson_decoder_state &state, PyObject **out_obj) {
    char uuid[16];
    memcpy(uuid, state.read(sizeof(uuid)), sizeof(uuid));

    switch (state.options.mode) {
        case bson_decoder_mode::JSON: {
            char buffer[36];
            format_uuid(uuid, buffer);
            auto uuid_obj = make_string(buffer, 36);
            *out_obj = uuid_obj.release();
            break;
        }
        case bson_decoder_mode::EXTENDED_JSON: {
            auto dict = make_dict();
            char buffer[36];
            format_uuid(uuid, buffer);
            auto uuid_str = make_string(buffer, 36);
            dict_set_item(dict.get(), "$uuid", uuid_str.get());
            *out_obj = dict.release();
            break;
        }
        case bson_decoder_mode::PYTHON: {
            auto uuid_obj = PyUuid_FromUUID(uuid);
            if (!uuid_obj) throw std::runtime_error("Failed to create uuid object");
            *out_obj = uuid_obj;
            break;
        }
    }
}

/* Decoder */

int32_t bson_read_value(bson_type type, bson_decoder_state &state, PyObject **out_obj) {
    switch (type) {
        case bson_type::BSON_TYPE_STRING:
            return bson_read_string_value(state, out_obj);
        case bson_type::BSON_TYPE_INT32:
            return bson_read_int32_value(state, out_obj);
        case bson_type::BSON_TYPE_INT64:
            return bson_read_int64_value(state, out_obj);
        case bson_type::BSON_TYPE_DOUBLE:
            return bson_read_float_value(state, out_obj);
        case bson_type::BSON_TYPE_BOOL:
            return bson_read_boolean_value(state, out_obj);
        case bson_type::BSON_TYPE_OBJECT:
            return bson_read_object_value(state, out_obj);
        case bson_type::BSON_TYPE_ARRAY:
            return bson_read_array_value(state, out_obj);
        case bson_type::BSON_TYPE_NULL:
            *out_obj = Py_None;
            Py_INCREF(Py_None);
            return 0;
        case bson_type::BSON_TYPE_BINARY:
            return bson_read_binary_value(state, out_obj);
        case bson_type::BSON_TYPE_UTC_DATETIME:
            return bson_read_datetime_value(state, out_obj);
        case bson_type::BSON_TYPE_OBJECTID:
            return bson_read_objectid_value(state, out_obj);
        case bson_type::BSON_TYPE_REGEX:
            return bson_read_regex_value(state, out_obj);
        // deprecated types
        case bson_type::__BSON_TYPE_UNDEFINED:
        case bson_type::__BSON_TYPE_DBPOINTER:
        case bson_type::__BSON_TYPE_SYMBOL:
        // unsupported types
        case bson_type::BSON_TYPE_JAVASCRIPT:
        case bson_type::BSON_TYPE_TIMESTAMP:
        case bson_type::BSON_TYPE_DECIMAL128:
        case bson_type::BSON_TYPE_MINKEY:
        case bson_type::BSON_TYPE_MAXKEY:
            *out_obj = Py_None;
            Py_INCREF(Py_None);
            return 0;
        default:
            throw py::value_error("Unsupported type: " + std::to_string(static_cast<uint8_t>(type)));
    }
}

py::dict decode(const py::bytes &data, const bson_decoder_mode &mode, const py::int_ &max_depth) {
    PyObject *data_ptr = data.ptr();
    bson_decoder_options options = {
        .max_depth = max_depth,
        .mode = mode,
    };

    char *buffer;
    Py_ssize_t buffer_size;
    if (PyBytes_AsStringAndSize(data_ptr, &buffer, &buffer_size) == -1)
        throw std::runtime_error("Failed to get buffer");

    bson_decoder_state state(options, reinterpret_cast<const uint8_t *>(buffer), buffer_size);

    PyObject *obj;
    auto read_len = bson_read_value(bson_type::BSON_TYPE_OBJECT, state, &obj);
    if (read_len != buffer_size) {
        Py_DECREF(obj);
        throw py::value_error("Invalid BSON data: Document length mismatch. (" + std::to_string(read_len) +
                              " != " + std::to_string(buffer_size) + ")");
    }

    return py::reinterpret_steal<py::dict>(obj);
}
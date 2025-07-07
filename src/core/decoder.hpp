#pragma once

#include <pybind11/pybind11.h>

#include "bson.hpp"
#include "portable_endian.hpp"
#include "utils.hpp"

namespace py = pybind11;

enum class bson_decoder_mode : uint8_t { JSON, EXTENDED_JSON, PYTHON };

struct bson_decoder_options {
    size_t max_depth;
    bson_decoder_mode mode;
};

struct bson_decoder_state {
    bson_decoder_options options;
    size_t offset;

    inline bson_decoder_state(const bson_decoder_options &options, const uint8_t *buffer, size_t buffer_size)
        : options(options), offset(0), cur_depth_(0), buffer_(buffer), buffer_size_(buffer_size) {}

    inline std::string make_error_msg(const std::string &reason) const {
        return "BSON decode error at offset " + std::to_string(offset) + ": " + reason;
    }

    inline std::string make_error_msg(const std::string &reason, const std::string &detail) const {
        return "BSON decode error at offset " + std::to_string(offset) + ": " + reason + " (" + detail + ")";
    }

    inline std::string make_bounds_error_msg(size_t required_bytes) const {
        return make_error_msg("Buffer underrun", "need " + std::to_string(required_bytes) + " bytes, " + "but only " +
                                                     std::to_string(buffer_size_ - offset) + " available");
    }

    inline void enter() {
        // root object is not counted
        if (cur_depth_ >= options.max_depth + 1) throw py::value_error("Maximum recursion depth exceeded");
        cur_depth_++;
    }

    inline void exit() {
        if (!cur_depth_) throw py::value_error("Broken call stack");
        cur_depth_--;
    }

    inline void skip(size_t size) {
        offset += size;
        if (offset > buffer_size_) throw py::value_error(make_bounds_error_msg(size));
    }

    template <typename T>
    inline const T *read() {
        auto ptr = buffer_ + offset;
        offset += sizeof(T);
        if (offset > buffer_size_) throw py::value_error(make_bounds_error_msg(sizeof(T)));
        return reinterpret_cast<const T *>(ptr);
    }

    inline const uint8_t *read(size_t size) {
        auto ptr = buffer_ + offset;
        offset += size;
        if (offset > buffer_size_) throw py::value_error(make_bounds_error_msg(size));
        return ptr;
    }

    inline void read_string(const char **value, size_t *value_size) {
        auto ptr = reinterpret_cast<const char *>(buffer_ + offset);
        auto max_len = buffer_size_ - offset;
        auto len = cstrnlen(ptr, max_len);
        if (len == max_len)
            throw py::value_error(make_error_msg("String not null-terminated", "string extends to end of buffer"));
        *value = ptr;
        *value_size = len;
        offset += len + 1;  // nul terminator
    }

    template <typename T>
    inline void read_little_endian(T *value) {
        *value = from_little_endian(*reinterpret_cast<const T *>(buffer_ + offset));
        offset += sizeof(T);
        if (offset > buffer_size_) throw py::value_error(make_bounds_error_msg(sizeof(T)));
    }

   private:
    const uint8_t *buffer_;
    size_t buffer_size_;
    size_t cur_depth_;
};

/* String Reader */

int32_t bson_read_string_value(bson_decoder_state &state, PyObject **out_obj);

/* Integer Reader */

int32_t bson_read_int32_value(bson_decoder_state &state, PyObject **out_obj);
int32_t bson_read_int64_value(bson_decoder_state &state, PyObject **out_obj);

/* Float Reader */

int32_t bson_read_float_value(bson_decoder_state &state, PyObject **out_obj);

/* Boolean Reader */

int32_t bson_read_boolean_value(bson_decoder_state &state, PyObject **out_obj);

/* Object Reader */

int32_t bson_read_object_value(bson_decoder_state &state, PyObject **out_obj);

/* Array Reader */

int32_t bson_read_array_value(bson_decoder_state &state, PyObject **out_obj);

/* DateTime Reader */

int32_t bson_read_datetime_value(bson_decoder_state &state, PyObject **out_obj);

/* ObjectId Reader */

int32_t bson_read_objectid_value(bson_decoder_state &state, PyObject **out_obj);

/* Regex Reader */

int32_t bson_read_regex_value(bson_decoder_state &state, PyObject **out_obj);

/* Binary Reader */

int32_t bson_read_binary_value(bson_decoder_state &state, PyObject **out_obj);
void bson_read_generic_binary_value(bson_subtype subtype, int32_t size, bson_decoder_state &state, PyObject **out_obj);
void bson_read_uuid_value(bson_decoder_state &state, PyObject **out_obj);

/* Decoder */

int32_t bson_read_value(bson_type type, bson_decoder_state &state, PyObject **out_obj);

py::dict decode(const py::bytes &data, const bson_decoder_mode &mode, const py::int_ &max_depth);

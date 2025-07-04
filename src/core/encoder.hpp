#pragma once

#include <pybind11/pybind11.h>

#include "bson.hpp"
#include "utils.hpp"

namespace py = pybind11;

constexpr size_t INITIAL_BUFFER_SIZE = sizeof(int32_t) + 1 + 256 + 1;
constexpr size_t MAX_CONTEXT_BUFFER_SIZE = 1024 * 1024 * 3;

struct bson_encoder_options {
    bool skipkeys;
    bool sort_keys;
    bool allow_nan;
    bool check_circular;
    size_t max_depth;
};

struct bson_encoder_state {
    bson_encoder_options options;
    size_t offset;

    inline bson_encoder_state(const bson_encoder_options &options, size_t buffer_size, size_t max_size)
        : options(options),
          offset(0),
          buffer_(static_cast<uint8_t *>(malloc(buffer_size))),
          buffer_size_(buffer_size),
          max_size_(max_size),
          stack_(),
          cur_depth_(0) {
        if (!buffer_) throw std::runtime_error("Failed to allocate buffer");

        if (options.check_circular) {
            stack_.reserve(std::clamp(options.max_depth / 2, static_cast<size_t>(1), static_cast<size_t>(10)));
        }
    }

    inline ~bson_encoder_state() { free(buffer_); }

    inline void enter(PyObject *obj) {
        if (options.check_circular) {
            if (std::find(stack_.begin(), stack_.end(), obj) != stack_.end())
                throw py::value_error("Circular reference detected");
            stack_.push_back(obj);
        }
        // root object is not counted
        if (cur_depth_ >= options.max_depth + 1) throw py::value_error("Maximum recursion depth exceeded");
        cur_depth_++;
    }

    inline void exit(PyObject *obj) {
        if (options.check_circular) {
            if (stack_.empty() || stack_.back() != obj) throw py::value_error("Broken call stack");
            stack_.pop_back();
        }
        if (!cur_depth_) throw py::value_error("Broken call stack");
        cur_depth_--;
    }

    template <typename T>
    inline size_t reserve() {
        if (offset + sizeof(T) > buffer_size_) overflow(sizeof(T));
        auto cur_offset = offset;
        offset += sizeof(T);
        return cur_offset;
    }

    template <typename T>
    inline void insert_byte(size_t offset, T value) {
        static_assert(sizeof(T) == 1, "T must be 1 byte");
        if (offset + sizeof(T) > buffer_size_) throw std::overflow_error("Buffer overflow");
        buffer_[offset] = static_cast<uint8_t>(value);
        offset += sizeof(T);
    }

    template <typename T>
    inline void insert_little_endian(size_t offset, T value) {
        if (offset + sizeof(T) > buffer_size_) throw std::overflow_error("Buffer overflow");
        T converted_value = to_little_endian(value);
        memcpy(buffer_ + offset, &converted_value, sizeof(T));
        offset += sizeof(T);
    }

    template <typename T>
    inline void write_byte(T value) {
        static_assert(sizeof(T) == 1, "T must be 1 byte");
        if (offset + sizeof(T) > buffer_size_) overflow(sizeof(T));
        buffer_[offset] = static_cast<uint8_t>(value);
        offset += sizeof(T);
    }

    inline void write(const void *value, size_t size) {
        if (offset + size > buffer_size_) overflow(size);
        memcpy(buffer_ + offset, value, size);
        offset += size;
    }

    template <typename T>
    inline void write_little_endian(T value) {
        if (offset + sizeof(T) > buffer_size_) overflow(sizeof(T));
        T converted_value = to_little_endian(value);
        memcpy(buffer_ + offset, &converted_value, sizeof(T));
        offset += sizeof(T);
    }

    inline void write_nul_terminator() {
        if (offset + sizeof(BSON_NUL_TERM) > buffer_size_) overflow(sizeof(BSON_NUL_TERM));
        buffer_[offset] = BSON_NUL_TERM;
        offset += sizeof(BSON_NUL_TERM);
    }

    inline uint8_t *buffer() const { return buffer_; }
    inline size_t buffer_size() const { return buffer_size_; }
    inline size_t size() const { return offset; }
    inline size_t max_size() const { return max_size_; }

    inline void clear() {
        if (!offset && !cur_depth_) return;
        offset = 0;
        cur_depth_ = 0;
        stack_.clear();

        auto new_buffer_size =
            std::clamp(buffer_size_, INITIAL_BUFFER_SIZE, std::min(max_size_, MAX_CONTEXT_BUFFER_SIZE));

        if (new_buffer_size != buffer_size_) {
            auto new_buffer = static_cast<uint8_t *>(realloc(buffer_, new_buffer_size));
            if (!new_buffer) throw std::runtime_error("Failed to reallocate buffer");
            buffer_ = new_buffer;
            buffer_size_ = new_buffer_size;
        }
    }

   private:
    uint8_t *buffer_;
    size_t buffer_size_;
    size_t max_size_;
    std::vector<PyObject *> stack_;
    size_t cur_depth_;

    inline void overflow(size_t size) {
        if (offset + size > max_size_) throw py::value_error("The BSON document size exceeds the maximum allowed size");
        buffer_size_ = std::clamp(buffer_size_ * 3 / 2, offset + size, max_size_);
        auto new_buffer = static_cast<uint8_t *>(realloc(buffer_, buffer_size_));
        if (!new_buffer) throw std::runtime_error("Failed to reallocate buffer");
        buffer_ = new_buffer;
    }
};

/* String Writer */

int32_t bson_write_string_value(PyObject *obj, bson_encoder_state &state, size_t out_type_offset);

/* Integer Writer */

int32_t bson_write_integer_value(PyObject *obj, bson_encoder_state &state, size_t out_type_offset);

/* Float Writer */

int32_t bson_write_float_value(PyObject *obj, bson_encoder_state &state, size_t out_type_offset);

/* Boolean Writer */

int32_t bson_write_boolean_value(PyObject *obj, bson_encoder_state &state, size_t out_type_offset);

/* Object Writer */

int32_t bson_write_object_value(PyObject *obj, bson_encoder_state &state, size_t out_type_offset);

/* Array Writer */

int32_t bson_write_array_value(PyObject *obj, bson_encoder_state &state, size_t out_type_offset);

/* DateTime Writer */

int32_t bson_write_datetime_value(PyObject *obj, bson_encoder_state &state, size_t out_type_offset);

/* Regex Writer */

int32_t bson_write_regex_value(PyObject *obj, bson_encoder_state &state, size_t out_type_offset);

/* Binary Writer */

int32_t bson_write_binary_value(PyObject *obj, bson_encoder_state &state, size_t out_type_offset);

/* UUID Writer */

int32_t bson_write_uuid_value(PyObject *obj, bson_encoder_state &state, size_t out_type_offset);

/* Encoder */

int32_t bson_write_value(PyObject *obj, bson_encoder_state &state, size_t out_type_offset);

py::bytes encode(const py::object &obj, const py::bool_ &skipkeys, const py::bool_ &check_circular,
                 const py::bool_ &allow_nan, const py::bool_ &sort_keys, const py::int_ &max_depth,
                 const py::int_ &max_size);

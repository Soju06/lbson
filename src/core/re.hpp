#pragma once

#include <Python.h>

#include "utils.hpp"

extern struct py_re_module {
    PyObject *module;
    PyObject *compile;
    PyTypeObject *pattern_type;

    struct {
        int32_t IGNORECASE;
        int32_t MULTILINE;
        int32_t DOTALL;
        int32_t UNICODE;
        int32_t VERBOSE;
        int32_t DEBUG;
    } flags;
} g_re_module;

#define PyRe_Module g_re_module.module
#define PyRe_PatternType g_re_module.pattern_type
#define PyPattern_Check(obj) PyObject_TypeCheck((obj), PyRe_PatternType)

#define PyRe_IMPORT PyRe_Import()

inline void PyRe_Import() {
    g_re_module.module = PyImport_ImportModule("re");
    if (!g_re_module.module) throw std::runtime_error("Failed to import re module");

    g_re_module.compile = PyObject_GetAttrString(g_re_module.module, "compile");
    if (!g_re_module.compile) throw std::runtime_error("Failed to get compile attribute");

    g_re_module.pattern_type = reinterpret_cast<PyTypeObject *>(PyObject_GetAttrString(g_re_module.module, "Pattern"));
    if (!g_re_module.pattern_type) throw std::runtime_error("Failed to get Pattern type");

#define GET_FLAG(name)                                                      \
    {                                                                       \
        PyObject *flag = PyObject_GetAttrString(g_re_module.module, #name); \
        if (!flag) {                                                        \
            Py_DECREF(flag);                                                \
            throw std::runtime_error("Failed to get " #name " attribute");  \
        }                                                                   \
        g_re_module.flags.name = PyLong_AsLong(flag);                       \
        Py_DECREF(flag);                                                    \
    }
    GET_FLAG(IGNORECASE);
    GET_FLAG(MULTILINE);
    GET_FLAG(DOTALL);
    GET_FLAG(UNICODE);
    GET_FLAG(VERBOSE);
    GET_FLAG(DEBUG);
#undef GET_FLAG
}

inline int32_t PyRe_GetFlag(const char *flag, size_t flag_len) {
    if (!g_re_module.module) return 0;
    int32_t flag_value = 0;

    for (size_t i = 0; i < flag_len; i++) {
        switch (flag[i]) {
            case 'i':
                flag_value |= g_re_module.flags.IGNORECASE;
                break;
            case 'm':
                flag_value |= g_re_module.flags.MULTILINE;
                break;
            case 's':
                flag_value |= g_re_module.flags.DOTALL;
                break;
            case 'x':
                flag_value |= g_re_module.flags.VERBOSE;
                break;
            case 'u':
                flag_value |= g_re_module.flags.UNICODE;
                break;
        }
    }

    return flag_value;
}

inline size_t PyRe_GetFlagString(int32_t flag, char *out_flags, size_t out_flags_len) {
    if (out_flags_len < 5) return 0;

    size_t i = 0;

    if (flag & g_re_module.flags.IGNORECASE && i < out_flags_len) out_flags[i++] = 'i';
    if (flag & g_re_module.flags.MULTILINE && i < out_flags_len) out_flags[i++] = 'm';
    if (flag & g_re_module.flags.DOTALL && i < out_flags_len) out_flags[i++] = 's';
    if (flag & g_re_module.flags.VERBOSE && i < out_flags_len) out_flags[i++] = 'x';
    if (flag & g_re_module.flags.UNICODE && i < out_flags_len) out_flags[i++] = 'u';

    return i;
}

inline PyObject *PyRe_Compile(const char *pattern, size_t pattern_len, const char *flags, size_t flags_len) {
    if (!g_re_module.compile) return nullptr;
    py_obj_ptr pattern_obj(PyUnicode_FromStringAndSize(pattern, pattern_len));
    py_obj_ptr flags_obj(PyLong_FromLong(PyRe_GetFlag(flags, flags_len)));

    PyObject *args[2] = {pattern_obj.get(), flags_obj.get()};
    PyObject *result = PyObject_Vectorcall(g_re_module.compile, args, 2, nullptr);
    if (!result) return nullptr;
    return result;
}

inline void PyRe_Module_CleanUp() {
    if (g_re_module.module) Py_DECREF(g_re_module.module);
    if (g_re_module.compile) Py_DECREF(g_re_module.compile);
    if (g_re_module.pattern_type) Py_DECREF(g_re_module.pattern_type);
    g_re_module = {};
}

#define PyRe_CLEANUP PyRe_Module_CleanUp()

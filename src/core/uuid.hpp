#pragma once

#include <Python.h>

#include <cstring>

#include "utils.hpp"

extern struct py_uuid_module {
    PyObject *module;
    PyTypeObject *uuid_type;
} g_uuid_module;

#define PyUuid_Module g_uuid_module.module
#define PyUuid_UUIDType g_uuid_module.uuid_type
#define PyUUID_Check(obj) PyObject_TypeCheck((obj), PyUuid_UUIDType)

#define PyUuid_IMPORT PyUuid_Import()

inline void PyUuid_Import() {
    g_uuid_module.module = PyImport_ImportModule("uuid");
    if (!g_uuid_module.module) throw std::runtime_error("Failed to import uuid module");

    g_uuid_module.uuid_type = reinterpret_cast<PyTypeObject *>(PyObject_GetAttrString(g_uuid_module.module, "UUID"));
    if (!g_uuid_module.uuid_type) throw std::runtime_error("Failed to get UUID type");
}

inline PyObject *PyUuid_FromUUID(const char uuid[16]) {
    py_obj_ptr uuid_bytes(PyBytes_FromStringAndSize(reinterpret_cast<const char *>(uuid), 16));
    if (!uuid_bytes) return nullptr;

    py_obj_ptr kwnames(PyTuple_New(1));
    if (!kwnames) return nullptr;
    auto bytes_obj = make_interned_string("bytes");
    PyTuple_SET_ITEM(kwnames.get(), 0, bytes_obj.release());

    PyObject *args[1] = {uuid_bytes.get()};
    py_obj_ptr result(PyObject_Vectorcall(reinterpret_cast<PyObject *>(PyUuid_UUIDType), args, 0, kwnames.get()));
    if (!result) return nullptr;

    return result.release();
}

inline int PyUuid_AsUUID(PyObject *obj, char uuid[16]) {
    py_obj_ptr bytes_attr(PyObject_GetAttrString(obj, "bytes"));
    if (!bytes_attr || !PyBytes_Check(bytes_attr.get())) return -1;

    auto size = PyBytes_GET_SIZE(bytes_attr.get());
    if (size != 16) return -1;

    auto bytes_data = PyBytes_AS_STRING(bytes_attr.get());
    if (!bytes_data) return -1;

    memcpy(uuid, bytes_data, 16);
    return 0;
}

inline void PyUuid_Module_CleanUp() {
    if (g_uuid_module.module) Py_DECREF(g_uuid_module.module);
    if (g_uuid_module.uuid_type) Py_DECREF(g_uuid_module.uuid_type);
    g_uuid_module = {};
}

#define PyUuid_CLEANUP PyUuid_Module_CleanUp()

// clang-format off
#include <pybind11/pybind11.h>
#include <datetime.h>
// clang-format on

#include <cstdlib>

#include "decoder.hpp"
#include "encoder.hpp"
#include "utils.hpp"

// clang-format off
#include "re.hpp"
#include "uuid.hpp"
// clang-format on

#define STRINGIFY(x) #x
#define MACRO_STRINGIFY(x) STRINGIFY(x)

namespace py = pybind11;

PyDateTime_CAPI *g_PyDateTimeAPI = nullptr;
py_re_module g_re_module{};
py_uuid_module g_uuid_module{};

void module_cleanup() {
    g_PyDateTimeAPI = nullptr;
    PyRe_CLEANUP;
    PyUuid_CLEANUP;
}

PYBIND11_MODULE(_core, m) {
    PyDateTime_IMPORT;
    g_PyDateTimeAPI = PyDateTimeAPI;
    PyRe_IMPORT;
    PyUuid_IMPORT;

    /*
     * BSON decoder mode enum
     */

    py::enum_<bson_decoder_mode>(m, "DecoderMode")
        .value("JSON", bson_decoder_mode::JSON)
        .value("EXTENDED_JSON", bson_decoder_mode::EXTENDED_JSON)
        .value("PYTHON", bson_decoder_mode::PYTHON);

    /*
     * BSON encoder
     */

    m.def("encode", &encode, py::arg("obj").noconvert().none(false), py::kw_only(), py::arg("skipkeys") = false,
          py::arg("check_circular") = true, py::arg("allow_nan") = true, py::arg("sort_keys") = false,
          py::arg("max_depth") = INT32_MAX, py::arg("max_size") = INT32_MAX, py::return_value_policy::take_ownership);

    /*
     * BSON decoder
     */

    m.def("decode", &decode, py::arg("data").noconvert().none(false), py::kw_only(),
          py::arg("mode") = py::cast(bson_decoder_mode::PYTHON), py::arg("max_depth") = INT32_MAX,
          py::return_value_policy::take_ownership);

#ifdef VERSION_INFO
    m.attr("__version__") = MACRO_STRINGIFY(VERSION_INFO);
#else
    m.attr("__version__") = "dev";
#endif

    auto atexit = py::module_::import("atexit");
    atexit.attr("register")(py::cpp_function([]() { module_cleanup(); }));
}
#include <pybind11/pybind11.h>
PYBIND11_MODULE(sdk_extension, module, pybind11::mod_gil_not_used()) {
    module.def("answer", [] { return 42; });
}

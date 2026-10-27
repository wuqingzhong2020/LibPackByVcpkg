#include <pybind11/embed.h>
int main(int argc, char** argv) {
    pybind11::scoped_interpreter guard{};
    pybind11::globals()["sdk_expected_debug"] = bool(SDK_PYTHON_DEBUG);
    pybind11::exec(R"(
import sys, sysconfig, ctypes, decimal, zlib, hashlib
assert sys.version_info[:3] == (3, 15, 2), sys.version
assert hasattr(sys, 'gettotalrefcount') == sdk_expected_debug, 'Python Debug/Release runtime mismatch'
assert sysconfig.get_config_var('Py_GIL_DISABLED') == 1
assert not sys._is_gil_enabled()
assert decimal.Decimal('0.1') + decimal.Decimal('0.2') == decimal.Decimal('0.3')
assert ctypes.sizeof(ctypes.c_void_p) == 8
payload = b'C++20 SDK' * 100
assert zlib.decompress(zlib.compress(payload)) == payload
assert len(hashlib.sha256(payload).digest()) == 32
)");
    if(argc>1) {
        pybind11::module_::import("sys").attr("path").attr("insert")(0,argv[1]);
        if(pybind11::module_::import("sdk_extension").attr("answer")().cast<int>()!=42) return 1;
    }
    if(pybind11::module_::import("sys").attr("_is_gil_enabled")().cast<bool>()) return 1;
}

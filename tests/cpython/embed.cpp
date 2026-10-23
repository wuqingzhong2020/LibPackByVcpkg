#include <Python.h>

int main(int argc, char** argv) {
    // Keep PYTHONHOME/PYTHONPATH supplied by the SDK test runner, while passing
    // the same script and arguments used by the standalone interpreter.
    PyConfig config;
    PyConfig_InitPythonConfig(&config);
    config.write_bytecode = 0;
    PyStatus status = PyConfig_SetBytesArgv(&config, argc, argv);
    if (!PyStatus_Exception(status)) status = Py_InitializeFromConfig(&config);
    PyConfig_Clear(&config);
    if (PyStatus_Exception(status)) Py_ExitStatusException(status);
    return Py_RunMain();
}

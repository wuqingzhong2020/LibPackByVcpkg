#include <Python.h>

static PyObject* answer(PyObject*, PyObject*) { return PyLong_FromLong(42); }
static PyMethodDef methods[] = {
    {"answer", answer, METH_NOARGS, nullptr},
    {nullptr, nullptr, 0, nullptr}
};
static PyModuleDef_Slot slots[] = {
    {Py_mod_gil, Py_MOD_GIL_NOT_USED},
    {0, nullptr}
};
static PyModuleDef module = {
    PyModuleDef_HEAD_INIT, "sdk_cpython_extension", nullptr, 0, methods, slots,
    nullptr, nullptr, nullptr
};
PyMODINIT_FUNC PyInit_sdk_cpython_extension() { return PyModuleDef_Init(&module); }

#define PY_SSIZE_T_CLEAN
#include "Python.h"

#if PY_MAJOR_VERSION >= 3
#   define MOD_RETURN(mod) return mod;
#   define MODINIT_NAME PyInit__djb_hash
#   define BUFFERLIKE_FMT "y#"
#else
#   define MOD_RETURN(mod) return;
#   define MODINIT_NAME init_djb_hash
#   define BUFFERLIKE_FMT "t#"
#endif

/* Return a Python long instance containing the value of the DJB hash function
 * for the given string or array. */
static PyObject *
djb_hash(PyObject *self, PyObject *args)
{
    const unsigned char *s;
    unsigned int h = 5381;
    Py_ssize_t len;

    if(! PyArg_ParseTuple(args, BUFFERLIKE_FMT, &s, &len))
        return NULL;

    while(len--)
        h = ((h << 5) + h) ^ *s++;

    return PyLong_FromUnsignedLong((unsigned long) h);
}


static /*const*/ PyMethodDef module_methods[] = {
    {"djb_hash", djb_hash, METH_VARARGS,
     "Return the value of DJB's hash function for the given 8-bit string."},
    {NULL, NULL, 0, NULL}
};

#if PY_MAJOR_VERSION >= 3
static struct PyModuleDef moduledef = {
    PyModuleDef_HEAD_INIT,
    "_djb_hash",
    NULL,
    -1,
    module_methods,
    NULL,
    NULL,
    NULL,
    NULL
};
#endif

PyMODINIT_FUNC
MODINIT_NAME(void)
{
#if PY_MAJOR_VERSION >= 3
    PyObject *mod = PyModule_Create(&moduledef);
#else
    PyObject *mod = Py_InitModule3("_djb_hash", module_methods, "");
#endif

    MOD_RETURN(mod);
}

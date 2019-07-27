#define PY_SSIZE_T_CLEAN
#include "Python.h"

#define MOD_RETURN(mod) return mod;
#define MODINIT_NAME PyInit__djb_hash
#define BUFFERLIKE_FMT "y#"

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

PyMODINIT_FUNC
MODINIT_NAME(void)
{
    PyObject *mod = PyModule_Create(&moduledef);

    MOD_RETURN(mod);
}

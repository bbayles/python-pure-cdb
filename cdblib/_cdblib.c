#define PY_SSIZE_T_CLEAN
#include "Python.h"

/* Return a Python long instance containing the value of the DJB hash function
 * for the given string or array. */
static PyObject *
djb_hash(PyObject *self, PyObject *args)
{
    const unsigned char *s;
    unsigned int h = 5381;
    Py_ssize_t len;

    if(! PyArg_ParseTuple(args, "t#", &s, &len))
        return NULL;

    while(len--)
        h = ((h << 5) + h) ^ *s++;

    return PyLong_FromUnsignedLong((unsigned long) h);
}


static /*const*/ PyMethodDef methods[] = {
    {"djb_hash", djb_hash, METH_VARARGS,
     "Return the value of DJB's hash function for the given 8-bit string."},
    {NULL, NULL, 0, NULL}
};


PyMODINIT_FUNC
init_cdblib(void)
{
    Py_InitModule("_cdblib", methods);
}

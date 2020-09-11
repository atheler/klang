/**
 * Some ring buffer based Python filter objects.
 *   - ForwardCombFilter
 *   - BackwardCombFilter
 *   - EchoFilter
 *
 * Notes:
 *
 * Error types:
 *   - PyExc_RuntimeError
 *   - PyExc_ValueError
 */
#define PY_SSIZE_T_CLEAN
#include <Python.h>
#include "structmember.h"
#include <numpy/arrayobject.h>


const size_t MAX_RING_BUFFER_CAPACITY = 60 * 44100;
const double DEFAULT_ALPHA = .9;


/**
 * Ring buffer.
 *
 * Holds length many double values.
 * TODO:
 *   - length -> capacity / maxCapacity
 *   - Support for varying ring buffer length
 */
typedef struct {
    size_t length;
    size_t position;
    double data[];
} RingBuffer;


/**
 * Create new RingBuffer instance for a given length.
 */
RingBuffer* RingBuffer_create(size_t length)
{
    if (length > MAX_RING_BUFFER_CAPACITY) {
        perror("RingBuffer_create(): length parameter to large!");
        return NULL;
    }

    size_t size = sizeof(RingBuffer) + length * sizeof(double);
    RingBuffer *self = (RingBuffer *) malloc(size);
    if (!self) {
        perror("malloc RingBuffer");
        exit(EXIT_FAILURE);
    }

    self->length = length;
    self->position = 0;
    memset(self->data, 0., length * sizeof(double));
    return self;
}


/**
 * Destroy RingBuffer instance.
 */
void
RingBuffer_destroy(RingBuffer *self)
{
    free(self);
}


/**
 * Peek current value of RingBuffer.
 *
 * Without modfiying current read / write position.
 */
double
RingBuffer_peek(RingBuffer *self)
{
    return self->data[self->position];
}


/**
 * Append value to RingBuffer.
 */
void
RingBuffer_append(RingBuffer *self, double newValue)
{
    self->data[self->position++] = newValue;
    self->position %= self->length;
}


/**
 * Base Python object for all ring buffer based filters.
 */
typedef struct {
    PyObject_HEAD
    double alpha;  // Gain factor in feedback path
    RingBuffer* ringBuffer;
} RingBufferFilterObject;


static void
RingBufferFilter_dealloc(RingBufferFilterObject *self)
{
    RingBuffer_destroy(self->ringBuffer);
    Py_TYPE(self)->tp_free((PyObject *) self);
}


static PyObject *
RingBufferFilter_new(PyTypeObject *type, PyObject *args, PyObject *kwargs)
{
    static char *kwlist[] = {"length", "alpha", NULL};
    int length;
    double alpha = DEFAULT_ALPHA;
    if (!PyArg_ParseTupleAndKeywords(args, kwargs, "i|d", kwlist, &length, &alpha)) {
        PyErr_SetString(PyExc_RuntimeError, "Could not parse arguments!");
        return NULL;
    }

    RingBufferFilterObject *self;
    self = (RingBufferFilterObject *) type->tp_alloc(type, 0);
    if (!self) {
        PyErr_SetString(PyExc_RuntimeError, "Could not allocate RingBufferFilterObject!");
        return NULL;
    }

    self->alpha = alpha;
    self->ringBuffer = RingBuffer_create(length);
    if (!self->ringBuffer) {
        PyErr_SetString(PyExc_RuntimeError, "Could not initialize RingBuffer!");
        return NULL;
    }

    return (PyObject *) self;
}


static int
RingBufferFilter_init(RingBufferFilterObject *self, PyObject *args, PyObject *kwargs)
{
    static char *kwlist[] = {"length", "alpha", NULL};
    int length;
    if (!PyArg_ParseTupleAndKeywords(args, kwargs, "i|d", kwlist, &length, &self->alpha)) {
        return -1;
    }

    return 0;
}


// Attributes access


static PyMemberDef RingBufferFilter_members[] = {
    {
        "alpha",  // Name
        T_DOUBLE,  // ?
        offsetof(RingBufferFilterObject, alpha),
        0,  // Flag
        "Gain of comb filter"
    },
    {NULL},  /* Sentinel */
};


static PyObject *
RingBufferFilter_get_length(RingBufferFilterObject *self, void *closure)
{
    return PyLong_FromSsize_t(self->ringBuffer->length);
}


PyGetSetDef RingBufferFilter_getset[] = {
    {
        "length",  // name
         (getter) RingBufferFilter_get_length,  // getter
         NULL,  // setter
         "Length of underlying RingBuffer",  // doc
         NULL  // closure
    },
    {NULL},
};


/**
 * Parse input array from arg.
 */
static PyArrayObject *
parse_input_array(PyObject *args)
{
    PyArrayObject *inArray;
    if (!PyArg_Parse(args, "O", &inArray)) {
        PyErr_SetString(PyExc_RuntimeError, "Could not parse arguments!");
        return NULL;
    }

    inArray = PyArray_FROM_OT(inArray, NPY_DOUBLE);
    if (PyArray_NDIM(inArray) != 1) {
        PyErr_SetString(PyExc_ValueError, "samples have to be ndim 1!");
        return NULL;
    }

    return inArray;
}


/**
 * Initialize output array
 */
static PyArrayObject *
init_output_array(int nd, npy_intp *dims)
{
    PyArrayObject *outArray = PyArray_SimpleNew(nd, dims, NPY_DOUBLE);
    if (!outArray) {
        PyErr_SetString(PyExc_RuntimeError, "Couldn't build outArray array.");
        Py_XDECREF(outArray);
        return NULL;
    }

    return outArray;
}


// The slightly varying filter methods


static PyObject *
ForwardCombFilter_filter(RingBufferFilterObject *self, PyObject *args)
{
    PyArrayObject *inArray = parse_input_array(args);
    if (!inArray) {
        return NULL;
    }

    int nd = PyArray_NDIM(inArray);
    npy_intp *dims = PyArray_DIMS(inArray);
    PyArrayObject *outArray = init_output_array(nd, dims);
    if (!outArray) {
        return NULL;
    }

    double *x = PyArray_DATA(inArray);
    double *y = PyArray_DATA(outArray);
    for (int i = 0; i < dims[0]; ++i) {
        y[i] = x[i] + self->alpha * RingBuffer_peek(self->ringBuffer);
        RingBuffer_append(self->ringBuffer, x[i]);
    }

    return PyArray_Return(outArray);
}


static PyObject *
BackwardCombFilter_filter(RingBufferFilterObject *self, PyObject *args)
{
    PyArrayObject *inArray = parse_input_array(args);
    if (!inArray) {
        return NULL;
    }

    int nd = PyArray_NDIM(inArray);
    npy_intp *dims = PyArray_DIMS(inArray);
    PyArrayObject *outArray = init_output_array(nd, dims);
    if (!outArray) {
        return NULL;
    }

    double *x = PyArray_DATA(inArray);
    double *y = PyArray_DATA(outArray);
    for (int i = 0; i < dims[0]; ++i) {
        y[i] = x[i] + self->alpha * RingBuffer_peek(self->ringBuffer);
        RingBuffer_append(self->ringBuffer, y[i]);
    }

    return PyArray_Return(outArray);
}


static PyObject *
EchoFilter_filter(RingBufferFilterObject *self, PyObject *args)
{
    PyArrayObject *inArray = parse_input_array(args);
    if (!inArray) {
        return NULL;
    }

    int nd = PyArray_NDIM(inArray);
    npy_intp *dims = PyArray_DIMS(inArray);
    PyArrayObject *outArray = init_output_array(nd, dims);
    if (!outArray) {
        return NULL;
    }

    double *x = PyArray_DATA(inArray);
    double *y = PyArray_DATA(outArray);
    for (int i = 0; i < dims[0]; ++i) {
        y[i] = RingBuffer_peek(self->ringBuffer);
        RingBuffer_append(self->ringBuffer, self->alpha * y[i] + x[i]);
    }

    return PyArray_Return(outArray);
}


static PyMethodDef ForwardCombFilter_methods[] = {
    {
        "filter",
        (PyCFunction) ForwardCombFilter_filter,
        METH_O,
        "Forward filtering of samples",
    },
    {NULL, NULL, 0, NULL},
};


static PyMethodDef BackwardCombFilter_methods[] = {
    {
        "filter",
        (PyCFunction) BackwardCombFilter_filter,
        METH_O,
        "Backward filtering of samples",
    },
    {NULL, NULL, 0, NULL},
};


static PyMethodDef EchoFilter_methods[] = {
    {
        "filter",
        (PyCFunction) EchoFilter_filter,
        METH_O,
        "Backward filtering of samples",
    },
    {NULL, NULL, 0, NULL},
};


static PyTypeObject ForwardCombFilterType = {
    PyVarObject_HEAD_INIT(NULL, 0)
    .tp_basicsize = sizeof(RingBufferFilterObject),
    .tp_dealloc = (destructor) RingBufferFilter_dealloc,
    .tp_doc = "Feed forward comb filter",
    .tp_flags = Py_TPFLAGS_DEFAULT | Py_TPFLAGS_BASETYPE,
    .tp_getset = RingBufferFilter_getset,
    .tp_init = (initproc) RingBufferFilter_init,
    .tp_itemsize = 0,
    .tp_members = RingBufferFilter_members,
    .tp_methods = ForwardCombFilter_methods,
    .tp_name = "ForwardCombFilter",
    .tp_new = RingBufferFilter_new,
};


static PyTypeObject BackwardCombFilterType = {
    PyVarObject_HEAD_INIT(NULL, 0)
    .tp_basicsize = sizeof(RingBufferFilterObject),
    .tp_dealloc = (destructor) RingBufferFilter_dealloc,
    .tp_doc = "Feed backward comb filter",
    .tp_flags = Py_TPFLAGS_DEFAULT | Py_TPFLAGS_BASETYPE,
    .tp_getset = RingBufferFilter_getset,
    .tp_init = (initproc) RingBufferFilter_init,
    .tp_itemsize = 0,
    .tp_members = RingBufferFilter_members,
    .tp_methods = BackwardCombFilter_methods,
    .tp_name = "BackwardCombFilter",
    .tp_new = RingBufferFilter_new,
};


static PyTypeObject EchoFilterType = {
    PyVarObject_HEAD_INIT(NULL, 0)
    .tp_basicsize = sizeof(RingBufferFilterObject),
    .tp_dealloc = (destructor) RingBufferFilter_dealloc,
    .tp_doc = "Wet only echo filter",
    .tp_flags = Py_TPFLAGS_DEFAULT | Py_TPFLAGS_BASETYPE,
    .tp_getset = RingBufferFilter_getset,
    .tp_init = (initproc) RingBufferFilter_init,
    .tp_itemsize = 0,
    .tp_members = RingBufferFilter_members,
    .tp_methods = EchoFilter_methods,
    .tp_name = "EchoFilter",
    .tp_new = RingBufferFilter_new,
};


static PyModuleDef filtersModule = {
    PyModuleDef_HEAD_INIT,
    .m_name = "_filters",
    .m_doc = "C extension for ring buffer based audio filters",
    .m_size = -1,
};


PyMODINIT_FUNC
PyInit__filters(void)
{
    import_array();
    PyObject *module = PyModule_Create(&filtersModule);
    if (!module) {
        PyErr_SetString(PyExc_RuntimeError, "Could not create _filters module!");
        return NULL;
    }

    if (
        PyType_Ready(&ForwardCombFilterType)
        || PyType_Ready(&BackwardCombFilterType)
        || PyType_Ready(&EchoFilterType)
    ) {
        PyErr_SetString(PyExc_RuntimeError, "Could not prepare filter types!");
        Py_DECREF(module);
        return NULL;
    }

    Py_INCREF(&ForwardCombFilterType);
    Py_INCREF(&BackwardCombFilterType);
    Py_INCREF(&EchoFilterType);

    if (
        PyModule_AddObject(module, "ForwardCombFilter", (PyObject *) &ForwardCombFilterType)
        || PyModule_AddObject(module, "BackwardCombFilter", (PyObject *) &BackwardCombFilterType)
        || PyModule_AddObject(module, "EchoFilter", (PyObject *) &EchoFilterType)
    ) {
        PyErr_SetString(PyExc_RuntimeError, "Could not add types to _filters module!");
        Py_DECREF(&ForwardCombFilterType);
        Py_DECREF(&BackwardCombFilterType);
        Py_DECREF(&EchoFilterType);
        Py_DECREF(module);
        return NULL;
    }

    return module;
}

/**
 * Envelope generator extension type.
 *
 * Rework of the C++ envelope of Nigel Redmon
 *
 * Implements
 *
 * class Envelope:
 *     def __init__(self, attack, decay, sustain, release, dt, overshoot, retrigger, loop):
 *         ...
 *
 *     def trigger(self, trigger: bool):
 *         ...
 *
 *     def sample(self, bufferSize: int):
 *         ...
 *
 * Resources:
 *   - http://www.earlevel.com/main/2013/06/01/envelope-generators/
 *   - https://dsp.stackexchange.com/questions/54086/single-pole-iir-low-pass-filter-which-is-the-correct-formula-for-the-decay-coe
 *   - https://dsp.stackexchange.com/questions/28308/exponential-weighted-moving-average-time-constant/28314#28314
 *   - https://www.earlevel.com/main/2012/12/15/a-one-pole-filter/
 */
#define PY_SSIZE_T_CLEAN
#define NPY_NO_DEPRECATED_API NPY_1_7_API_VERSION
#include "stdbool.h"
#include <math.h>  // exp, log
#include <Python.h>
#include "structmember.h"
#include <numpy/arrayobject.h>


static const double UPPER = 1.;  /// Upper bound of envelope signal.
static const double LOWER = 0.;  /// Lower bound of envelope signal.


/**
 * Clip value to interval [lower, upper].
 *
 * Aka clamp(). No lower < upper check.
 *
 * @param value Number to clip.
 * @param lower Lower bound.
 * @param upper Upper bound.
 */
static double
clip(const double value, const double lower, const double upper)
{
    return fmin(fmax(value, lower), upper);
}


/**
 * Envelope stage.
 *
 * The different ADSR envelope stages (state machine).
 */
typedef enum {
    OFF,
    ATTACKING,
    DECAYING,
    SUSTAINING,
    RELEASING,
} Stage;


/**
 * Print stage.
 *
 * Print stage as string to stdout (via fprint).
 *
 * @param stage The envelope stage to print.
 */
static void print_stage(const Stage stage) __attribute__((unused));
static void
print_stage(const Stage stage)
{
    printf("stage: ");
    switch(stage) {
        case OFF:
            printf("OFF");
            break;
        case ATTACKING:
            printf("ATTACKING");
            break;
        case DECAYING:
            printf("DECAYING");
            break;
        case SUSTAINING:
            printf("SUSTAINING");
            break;
        case RELEASING:
            printf("RELEASING");
            break;
        default:
            printf("unknown");
            break;
    }
    printf("\n");
}


/**
 * Calculate exponential coefficient.
 *
 * @param rate Envelope curve rate. In number of samples.
 * @param overshoot Amount of overshoot.
 * @return Alpha coefficient for one pole filter. In interval [0., 1.]. Note
 * already 1 - alpha.
 */
static double
calculate_exponential_coefficient(const double rate, const double overshoot)
{
    if (rate <= 0.)
        return 0.;

    return exp(-log((1.0 + overshoot) / overshoot) / rate);
}


/**
 * Envelope class.
 */
typedef struct {
    PyObject_HEAD

    /**
     * @name Attributes
     */
    /*@{*/
    double attack;
    double decay;
    double sustain;
    double release;
    double dt;
    double overshoot;
    bool retrigger;
    bool loop;
    /*@}*/

    /**
     * @name Envelope state.
     */
    /*@{*/
    Stage stage;  /// Current envelope stage
    double value; /// Current envelope value
    /*@}*/

    /**
     * @name Coefficients and base values.
     */
    /*@{*/
    double attackCoef;
    double attackBase;
    double decayCoef;
    double decayBase;
    double releaseCoef;
    double releaseBase;
    /*@}*/
} Envelope;


static PyMemberDef Envelope_members[] = {
    {
        "retrigger",  /* name */
        T_BOOL,  /* type */
        offsetof(Envelope, retrigger),  /* offset */
        0,  /* flags */
        "Retrigger enabled",  /* docstring */
    },
    {
        "loop",  /* name */
        T_BOOL,  /* type */
        offsetof(Envelope, loop),  /* offset */
        0,  /* flags */
        "Loop enabled",  /* docstring */
    },
    {NULL}  /* Sentinel */
};


/**
 * Compute base value and coefficient values for attack, decay and release stage.
 */
static void
Envelope_compute_base_values_and_coefficients(Envelope *self)
{
    self->attackCoef = calculate_exponential_coefficient(self->attack / self->dt, self->overshoot);
    self->attackBase = (UPPER + self->overshoot) * (1. - self->attackCoef);

    self->decayCoef = calculate_exponential_coefficient(self->decay / self->dt, self->overshoot);
    self->decayBase = (self->sustain - self->overshoot) * (1. - self->decayCoef);

    self->releaseCoef = calculate_exponential_coefficient(self->release / self->dt, self->overshoot);
    self->releaseBase = (LOWER - self->overshoot) * (1. - self->releaseCoef);
}


// Note: Getters and setters for attack, decay, sustain and release. Via
// PyGetSetDef because we need to recompute the base values and coefficients.


/**
 * Attack time getter.
 */
static PyObject *
Envelope_get_attack(Envelope *self, void *closure)
{
    return PyFloat_FromDouble(self->attack);
}


/**
 * Attack time setter.
 *
 * Also recomputes base values and coefficients.
 */
static int
Envelope_set_attack(Envelope *self, PyObject *value, void *closure)
{
    double attack = PyFloat_AsDouble(value);
    if (PyErr_Occurred()) {
        PyErr_SetString(PyExc_ValueError, "Could not cast *value to double!");
        return -1;
    }

    if (attack < 0) {
        PyErr_SetString(PyExc_ValueError, "attack must be positive!");
        return -1;
    }

    self->attack = attack;
    Envelope_compute_base_values_and_coefficients(self);
    return 0;
}


/**
 * Decay time getter.
 */
static PyObject *
Envelope_get_decay(Envelope *self, void *closure)
{
    return PyFloat_FromDouble(self->decay);
}


/**
 * Decay time setter.
 *
 * Also recomputes base values and coefficients.
 */
static int
Envelope_set_decay(Envelope *self, PyObject *value, void *closure)
{
    double decay = PyFloat_AsDouble(value);
    if (PyErr_Occurred()) {
        PyErr_SetString(PyExc_ValueError, "Could not cast *value to double!");
        return -1;
    }

    if (decay < 0) {
        PyErr_SetString(PyExc_ValueError, "decay must be positive!");
        return -1;
    }

    self->decay = decay;
    Envelope_compute_base_values_and_coefficients(self);
    return 0;
}


/**
 * Sustain value getter.
 */
static PyObject *
Envelope_get_sustain(Envelope *self, void *closure)
{
    return PyFloat_FromDouble(self->sustain);
}


/**
 * Sustain value setter.
 *
 * Also recomputes base values and coefficients.
 */
static int
Envelope_set_sustain(Envelope *self, PyObject *value, void *closure)
{
    double sustain  = PyFloat_AsDouble(value);
    if (PyErr_Occurred()) {
        PyErr_SetString(PyExc_ValueError, "Could not cast *value to double!");
        return -1;
    }

    if (!(LOWER <= sustain && sustain <= UPPER)) {
        PyErr_SetString(PyExc_ValueError, "sustain not within bounds!");
        return -1;
    }

    self->sustain = sustain;
    Envelope_compute_base_values_and_coefficients(self);
    return 0;
}


/**
 * Release time getter.
 */
static PyObject *
Envelope_get_release(Envelope *self, void *closure)
{
    return PyFloat_FromDouble(self->release);
}


/**
 * Release time setter.
 *
 * Also recomputes base values and coefficients.
 */
static int
Envelope_set_release(Envelope *self, PyObject *value, void *closure)
{
    double release = PyFloat_AsDouble(value);
    if (PyErr_Occurred()) {
        PyErr_SetString(PyExc_ValueError, "Could not cast *value to double!");
        return -1;
    }

    if (release < 0) {
        PyErr_SetString(PyExc_ValueError, "release must be positive!");
        return -1;
    }

    self->release = release;
    Envelope_compute_base_values_and_coefficients(self);
    return 0;
}


/**
 * Overshoot value getter.
 */
static PyObject *
Envelope_get_overshoot(Envelope *self, void *closure)
{
    return PyFloat_FromDouble(self->overshoot);
}


/**
 * Overshoot value setter.
 *
 * Also recomputes base values and coefficients.
 */
static int
Envelope_set_overshoot(Envelope *self, PyObject *value, void *closure)
{
    double overshoot = PyFloat_AsDouble(value);
    if (PyErr_Occurred()) {
        PyErr_SetString(PyExc_ValueError, "Could not cast *value to double!");
        return -1;
    }

    if (overshoot < 0) {
        PyErr_SetString(PyExc_ValueError, "overshoot must be positive!");
        return -1;
    }

    self->overshoot = clip(overshoot, 1e-9, 1e9);
    Envelope_compute_base_values_and_coefficients(self);
    return 0;
}


/**
 * Envelope active state.
 *
 * Is envelope active? Get active state of envelope.
 */
static PyObject *
Envelope_get_active(Envelope* self, void* closure)
{
    //printf("Envelope_get_active()\n");
    if (self->stage)
        Py_RETURN_TRUE;
    else
        Py_RETURN_FALSE;
}


PyGetSetDef Envelope_getset[] = {
    {
        "attack",  /* name */
         (getter) Envelope_get_attack,  /* getter */
         (setter) Envelope_set_attack,  /* setter */
         "Attack time",  /* doc */
         NULL /* closure */
    },
    {
        "decay",  /* name */
         (getter) Envelope_get_decay,  /* getter */
         (setter) Envelope_set_decay,  /* setter */
         "Decay time",  /* doc */
         NULL /* closure */
    },
    {
        "sustain",  /* name */
         (getter) Envelope_get_sustain,  /* getter */
         (setter) Envelope_set_sustain,  /* setter */
         "Sustain level",  /* doc */
         NULL /* closure */
    },
    {
        "release",  /* name */
         (getter) Envelope_get_release,  /* getter */
         (setter) Envelope_set_release,  /* setter */
         "Release time",  /* doc */
         NULL /* closure */
    },
    {
        "overshoot",  /* name */
         (getter) Envelope_get_overshoot,  /* getter */
         (setter) Envelope_set_overshoot,  /* setter */
         "Overshoot value",  /* doc */
         NULL /* closure */
    },
    {
        "active",  /* name */
         (getter) Envelope_get_active,  /* getter */
         NULL,  /* setter */
         "Is envelope active?",  /* doc */
         NULL /* closure */
    },
    {NULL}  /* Sentinel */
};


/**
 * Envelope de-allocater.
 *
 */
static void
Envelope_dealloc(Envelope* self)
{
    //printf("Envelope_dealloc()\n");
    Py_TYPE(self)->tp_free((PyObject*)self);
}


/**
 * Envelope.__new__().
 *
 * Python constructor method.
 */
static PyObject *
Envelope_new(PyTypeObject *type, PyObject *args, PyObject *kwargs)
{
    //printf("Envelope_new()\n");
    Envelope *self;
    self = (Envelope *)type->tp_alloc(type, 0);
    if (self != NULL) {
        self->attack = 0.;
        self->decay = 0.;
        self->sustain = 0.;
        self->release = 0.;
        self->dt = 0.;

        self->overshoot = 1e-3;
        self->retrigger = false;
        self->loop = false;

        self->stage = OFF;
        self->value = 0.;

        self->attackCoef = 0.;
        self->attackBase = 0.;
        self->decayCoef = 0.;
        self->decayBase = 0.;
        self->releaseCoef = 0.;
        self->releaseBase = 0.;
    }

    return (PyObject *)self;
}


/**
 * Change envelope stage.
 *
 * Put envelope in another envelope stage.
 *
 * @param self Envelope instance.
 * @param stage New envelope stage.
 */
static void
Envelope_change_stage(Envelope *self, const Stage stage)
{
    //printf("Envelope_change_stage()\n");
    //print_stage(stage);
    self->stage = stage;
}


/**
 * Envelope.__init__().
 *
 * Python initializer method.
 */
static int
Envelope_init(Envelope *self, PyObject *args, PyObject *kwargs)
{
    //printf("Envelope_init()\n");
    static char *kwlist[] = {
        "attack", "decay", "sustain", "release", "dt", "overshoot", "retrigger",
        "loop", NULL
    };
    if (!PyArg_ParseTupleAndKeywords(args, kwargs, "ddddd|dpp", kwlist, &self->attack,
                &self->decay, &self->sustain, &self->release, &self->dt, &self->overshoot,
                &self->retrigger, &self->loop)
    )
        return -1;

    self->overshoot = clip(self->overshoot, 1e-9, 1e9);  // Headroom
    Envelope_compute_base_values_and_coefficients(self);
    if (self->loop)
        Envelope_change_stage(self, ATTACKING);

    return 0;
}


/**
 * Gate envelope (on / off).
 *
 * Change trigger state of envelope.
 *
 * Note: gate() instead of trigger() because we want to use the name trigger
 * within the Klang blocks.
 *
 * @param self Envelope instance.
 * @param args Trigger state (Python bool).
 */
static PyObject *
Envelope_gate(Envelope *self, PyObject *args)
{
    bool trigger = PyObject_IsTrue(args);
    //printf("Envelope_gate(%i)\n", trigger);
    if (!self->loop) {
        Stage stage = self->stage;
        if (trigger) {
            if (self->retrigger || stage == OFF || stage == RELEASING) {
                Envelope_change_stage(self, ATTACKING);
            }
        } else {
            if (stage == ATTACKING || stage == DECAYING || stage == SUSTAINING) {
                Envelope_change_stage(self, RELEASING);
            }
        }
    }

    Py_RETURN_NONE;
}


/**
 * Envelope single cycle.
 *
 * Step envelope forward by one cycle and get next single sample.
 *
 * @param self Envelope instance.
 * @return Next envelope sample.
 */
static double
Envelope_single_sample(Envelope *self)
{
    double newValue = 0.;
    switch(self->stage) {
        case OFF:
            newValue = LOWER;
            if (self->loop)
                Envelope_change_stage(self, ATTACKING);

            break;
        case ATTACKING:
            newValue = self->attackBase + self->value * self->attackCoef;
            if (newValue >= UPPER) {
                newValue = UPPER;
                Envelope_change_stage(self, DECAYING);
            }

            break;
        case DECAYING:
            newValue = self->decayBase + self->value * self->decayCoef;
            if (newValue <= self->sustain) {
                newValue = self->sustain;
                Envelope_change_stage(self, SUSTAINING);
            }

            break;
        case SUSTAINING:
            newValue = self->sustain;
            if (self->loop)
                Envelope_change_stage(self, RELEASING);

            break;
        case RELEASING:
            newValue = self->releaseBase + self->value * self->releaseCoef;
            if (newValue <= LOWER) {
                newValue = LOWER;
                if (self->loop) {
                    Envelope_change_stage(self, ATTACKING);
                } else {
                    Envelope_change_stage(self, OFF);
                }
            }
    }

    self->value = newValue;
    return newValue;
}


/**
 * Sample envelope.
 *
 * Get next BUFFER_SIZE many samples.
 *
 * @param self Envelope instance.
 * @param bufferSize Number of samples to return.
 * @return Numpy array.
 */
static PyObject *
Envelope_sample(Envelope *self, PyObject *bufferSize)
{
    //printf("Envelope.sample(...)\n");
    size_t length = PyLong_AsSize_t(bufferSize);
    if (PyErr_Occurred()) {
        PyErr_SetString(PyExc_ValueError, "Could not cast *bufferSize to size_t!");
        return NULL;
    }

    // Create new empty numpy array
    int nd = 1;
    npy_intp dims[1] = {length};
    PyArrayObject *array = (PyArrayObject *) PyArray_SimpleNew(nd, dims, NPY_DOUBLE);
    if (array == NULL) {
        PyErr_SetString(PyExc_RuntimeError, "Couldn't build output array.");
        Py_XDECREF(array);
        return NULL;
    }

    // Fill in envelope samples
    double *arrayData = (double *) PyArray_DATA(array);
    for (size_t i = 0; i < length; ++i) {
        arrayData[i] = Envelope_single_sample(self);
    }

    return PyArray_Return(array);
}


PyMethodDef Envelope_methods[] = {
    {
        "gate",  /* name */
        (PyCFunction)Envelope_gate,
        METH_O,  /* flags */
        "Trigger envelope",  /* docstring */
    },
    {
        "sample",  /* name */
        (PyCFunction)Envelope_sample,
        METH_O,  /* flags */
        "Get the next bufferSize many envelope samples",  /* docstring */
    },
    { NULL, NULL, 0, NULL }  /* Sentinel */
};


/**
 * Envelope type
 */
static PyTypeObject EnvelopeType = {
    PyVarObject_HEAD_INIT(NULL, 0)
    .tp_name = "klang.audio._envelope.Envelope",
    .tp_basicsize = sizeof(Envelope),
    .tp_dealloc = (destructor)Envelope_dealloc,
    .tp_flags = Py_TPFLAGS_DEFAULT | Py_TPFLAGS_BASETYPE,
    .tp_doc = "Envelope extension type",
    .tp_methods = Envelope_methods,
    .tp_members = Envelope_members,
    .tp_getset = Envelope_getset,
    .tp_init = (initproc)Envelope_init,
    .tp_new = Envelope_new,
};


static PyModuleDef envelopeModuleDef = {
    PyModuleDef_HEAD_INIT,
    "_envelope",  /* name */
    "Example module that creates an extension type.", /* docstring */
    -1,
    NULL  /* Sentinel */
};


/**
 * Init module.
 */
PyMODINIT_FUNC
PyInit__envelope(void)
{
    PyObject* module;
    if (PyType_Ready(&EnvelopeType) < 0)
        return NULL;

    module = PyModule_Create(&envelopeModuleDef);
    if (module == NULL)
        return NULL;

    import_array();

    Py_INCREF(&EnvelopeType);
    if (PyModule_AddObject(module, "Envelope", (PyObject *)&EnvelopeType)) {
        Py_DECREF(&EnvelopeType);
        Py_DECREF(module);
        return NULL;
    }

    return module;
}

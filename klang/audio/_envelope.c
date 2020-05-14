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
#include "stdbool.h"
#include <math.h>  // exp, log
#include <Python.h>
#include "structmember.h"
#include <numpy/arrayobject.h>


static const double UPPER = 1.;  /// Upper bound of envelope signal.
static const double LOWER = 0.;  /// Lower bound of envelope signal.


/**
 * Clip value between interval [lower, upper].
 */
double clip(const double value, const double lower, const double upper)
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
    //double attack;
    //double decay;
    double sustain;
    //double release;
    //double dt;
    //double overshoot;
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

    /* Helper */
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
    //{"attack", T_DOUBLE, offsetof(Envelope, attack), 0, "Attack time"},
    //{"decay", T_DOUBLE, offsetof(Envelope, decay), 0, "Decay time"},
    {
        "sustain",  /* name */
        T_DOUBLE,  /* type */
        offsetof(Envelope, sustain),  /* offset */
        0,  /* flags */
        "Sustain time",  /* docstring */
    },
    //{"release", T_DOUBLE, offsetof(Envelope, release), 0, "Release time"},
    //{"dt", T_DOUBLE, offsetof(Envelope, dt), 0, "Sampling interval"},
    {NULL}  /* Sentinel */
};


/**
 * Envelope de-allocater.
 *
 * TODO: Do we need this?
 */
static void
Envelope_dealloc(Envelope* self)
{
    Py_TYPE(self)->tp_free((PyObject*)self);
}


/**
 * Envelope.__new__().
 *
 * Constructor.
 */
static PyObject *
Envelope_new(PyTypeObject *type, PyObject *args, PyObject *kwargs)
{
    //printf("Envelope_new()\n");
    Envelope *self;
    self = (Envelope *)type->tp_alloc(type, 0);
    if (self != NULL)
    {
        //self->attack = 0.;
        //self->decay = 0.;
        self->sustain = 0.;
        //self->release = 0.;
        //self->dt = 0.;

        //self->overshoot = .5;
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
 * Initializer.
 */
static int
Envelope_init(Envelope *self, PyObject *args, PyObject *kwargs)
{
    //printf("Envelope_init()\n");
    double attack, decay, release, dt, overshoot;
    static char *kwlist[] = {
        "attack", "decay", "sustain", "release", "dt", "overshoot", "retrigger",
        "loop", NULL
    };
    if (!PyArg_ParseTupleAndKeywords(args, kwargs, "ddddd|dpp", kwlist, &attack,
                &decay, &self->sustain, &release, &dt, &overshoot,
                &self->retrigger, &self->loop)
    )
        return -1;

    overshoot = clip(overshoot, 1e-9, 1e9);  // Headroom
    if (self->loop)
        Envelope_change_stage(self, ATTACKING);

    // Calculate coefficients and base values
    self->attackCoef = calculate_exponential_coefficient(attack / dt, overshoot);
    self->attackBase = (UPPER + overshoot) * (1. - self->attackCoef);

    self->decayCoef = calculate_exponential_coefficient(decay / dt, overshoot);
    self->decayBase = (self->sustain - overshoot) * (1. - self->decayCoef);

    self->releaseCoef = calculate_exponential_coefficient(release / dt, overshoot);
    self->releaseBase = (LOWER - overshoot) * (1. - self->releaseCoef);
    return 0;
}



/**
 * Trigger envelope (on / off).
 *
 * Change trigger state of envelope.
 *
 * @param self Envelope instance.
 * @param args Trigger state (Python bool).
 */
static PyObject *
Envelope_trigger(Envelope *self, PyObject *args)
{
    bool trigger = PyObject_IsTrue(args);
    //printf("Envelope_trigger(%i)\n", trigger);
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

    return Py_BuildValue("");
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
            newValue = self->value;
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
            newValue = self->value;
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
 * @return Numpy array.
 */
static PyObject *
Envelope_sample(Envelope *self, PyObject *args)
{
    //printf("Envelope.sample(...)\n");
    // Fetch bufferSize argument
    // TODO: Switch to METH_O? How to cast PyObject -> int?
    int bufferSize;
    if (!PyArg_ParseTuple(args, "i", &bufferSize)) {
        return NULL;
    }

    // New numpy array
    int nd = 1;
    npy_intp dims[1] = {bufferSize};
    PyObject* array = PyArray_SimpleNew(nd, dims, NPY_DOUBLE);

    // Fill in samples
    double *arrayData = (double*)PyArray_DATA(array);
    for (int i = 0; i < bufferSize; ++i) {
        arrayData[i] = Envelope_single_sample(self);
    }

    return array;
}


PyMethodDef Envelope_methods[] = {
    {"trigger", (PyCFunction)Envelope_trigger, METH_O, "Trigger envelope"},
    {"sample", (PyCFunction)Envelope_sample, METH_VARARGS, "Get the next bufferSize many envelope samples"},
    {NULL}  /* Sentinel */
};


/**
 * Envelope type
 */
static PyTypeObject EnvelopeType = {
    PyVarObject_HEAD_INIT(NULL, 0)
    .tp_name = "klang.audio._envelope.Envelope",
    .tp_doc = "Envelope extension type",

    .tp_members = Envelope_members,
    .tp_methods = Envelope_methods,

    .tp_new = Envelope_new,
    .tp_init = (initproc)Envelope_init,

    .tp_basicsize = sizeof(Envelope),
    .tp_flags = Py_TPFLAGS_DEFAULT | Py_TPFLAGS_BASETYPE,
    .tp_dealloc = (destructor)Envelope_dealloc,
};


static PyModuleDef envelopeModuleDef = {
    PyModuleDef_HEAD_INIT, "_envelope", "Example module that creates an extension type.", -1,
    NULL, NULL, NULL, NULL, NULL  /* Sentinel */
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


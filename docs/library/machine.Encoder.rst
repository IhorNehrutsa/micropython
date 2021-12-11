.. currentmodule:: machine
.. _machine.Encoder:

class Encoder -- Quadrature Incremental Encoder
===============================================

This class provides an Quadrature Incremental Encoder service.
Wiki info at `Incremental encoder <https://en.wikipedia.org/wiki/Incremental_encoder>`_.

If your port does not support hardware encoder use `Quadrature incremental encoder based on machine.Pin interrupts <https://github.com/IhorNehrutsa/MicroPython-quadrature-incremental-encoder>`_.
See also Pin-interrupt-based encoders (and problems) from Peter Hinch `Incremental encoders <https://github.com/peterhinch/micropython-samples/blob/master/encoders/ENCODERS.md>`_.
There is also `Dave Hylands an STM specific hardware-Timer-based solution <https://github.com/dhylands/upy-examples/blob/master/encoder.py>`_.

Here is described a basics, commons for hadware-counters-based encoders of MicroPython ports:

    * :ref:`ESP32.Encoder <pcnt.Encoder>`
    * mimxrt.Encoder - under constructions
    * STM32.Encoder - TODO

Minimal example usage::

    from machine import Pin, Encoder

    enc = Encoder(id, Pin(0), Pin(1))  # create Quadrature Encoder object and start to encode input pulses
    enc.init(filter_ns=0)              # switch filtering off
    value = enc.value()                # get current Encoder value
    value = enc.value(0)               # get current Encoder value, set Encoder to 0
    enc.deinit()                       # turn off the Encoder

    print(enc)                         # show the Encoder object properties

Constructor
-----------

.. class:: Encoder(id, phase_a=machine.Pin, phase_b=machine.Pin, \*, keyword_arguments)

    Construct and return a new quadrature encoder object using the following parameters:

      - *id*. Values of *id* depend on a particular port and its hardware.
        Values 0, 1, etc. are commonly used to select hardware block #0, #1, etc.

      - *phase_a* and *phase_b* are the Quadrature encoder inputs, which are usually
        :ref:`machine.Pin <machine.Pin>` objects, but a port may allow other values,
        like integers or strings, which designate a Pin in the *machine.Pin* class.
        They may be omitted on ports which have predefined pins for *id*-specified hardware block.
        Keywords may be ommited, for example  Encoder(0, Pin(0), Pin(1)).

    Keyword arguments:

      - *filter_ns*\=value. Specifies a ns-value for the minimal time a signal has to be stable
        at the pulse input to be recognized. The largest value is port specific and is the default.
        If the specified value is greater than the largest value, then largest value is used.
        A value of 0 or negative sets the filter is switched off.

Methods
-------

.. method:: Encoder.init(keyword_arguments)

   Modify the settings of the Encoder object. See the **Constructor** for details about the parameters.

.. method:: Encoder.deinit()

   Stops the Encoder, disables interrupts and releases hardware resources used by the encoder.
   A Soft Reset deinitializes all Encoder's objects.

.. method:: Encoder.value([value])

   Get (and optional set) the Encoder value as signed integer.
   With no argument the actual Encoderr value are returned.

   With a single *value* argument the Encoder is set to that value.

Simple check of Encoder performance
`encoders_test.py <https://github.com/IhorNehrutsa/MicroPython-quadrature-incremental-encoder/blob/main/encoders_test.py>`_

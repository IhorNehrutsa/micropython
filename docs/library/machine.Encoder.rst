.. currentmodule:: machine
.. _machine.Encoder:

class Encoder -- Quadrature Incremental Encoder
===============================================

This class provides an Quadrature Incremental Encoder service.
Wiki info at `Incremental encoder <https://en.wikipedia.org/wiki/Incremental_encoder>`_.

If your port does not support hardware encoder use `Quadrature incremental encoder based on machine.Pin() interrupts <https://github.com/IhorNehrutsa/MicroPython-quadrature-incremental-encoder>`_.
See also Pin-interrupt-based encoders (and problems) from Peter Hinch `Incremental encoders <https://github.com/peterhinch/micropython-samples/blob/master/encoders/ENCODERS.md>`_.
There is also `Dave Hylands an STM specific hardware-Timer-based solution <https://github.com/dhylands/upy-examples/blob/master/encoder.py>`_.

Here is described a basics, commons for hadware-counters-based encoders of MicroPython ports:

    * :ref:`ESP32.Encoder <pcnt.Encoder>`
    * mimxrt.Encoder - under constructions
    * STM32.Encoder - TODO

Minimal example usage::

    from machine import Pin, Encoder

    enc = Encoder(id, Pin(0), Pin(1))  # create Quadrature Encoder object and start to encode input pulses
    value = enc.value()                # get current Encoder value
    enc.set_value(0)                   # set Encoder value to 0
    enc.deinit()                       # turn off the Encoder

    print(enc)                         # show the Encoder object properties

Constructor
-----------

.. class:: Encoder(id, phase_a=Pin(), phase_b=Pin(), \*, keyword_arguments)

    Construct and return a new quadrature encoder object using the following parameters:

      - *id*. Values of *id* depend on a particular port and its hardware.
        Values 0, 1, etc. are commonly used to select hardware block #0, #1, etc.

      - *phase_a* and *phase_b* are the Quadrature encoder inputs, which are usually
        :ref:`machine.Pin <machine.Pin>` objects, but a port may allow other values,
        like integers or strings, which designate a Pin in the *machine.Pin* class.
        They may be omitted on ports which have predefined pins for *id*-specified hardware block.

    Keyword arguments:

      - *filter*\=value. Specifies a ns-value for the minimal time a signal has to be stable
        at the pulse input to be recognized. The largest value is port specific and is the default.
        If the specified value is greater than the largest value, then largest value is used.
        A value of 0 or negative sets the filter is switched off.

      - *x124*\=value. Possible values is 1, 2, 4. Default value is 4.
        More info in `Quadrature decoder state table <https://en.wikipedia.org/wiki/Incremental_encoder#Quadrature_decoder>`_.
        When more Encoder resolution is needed, it is possible for the encoder to count the leading
        and trailing edges of the quadrature encoder’s pulse train from one channel,
        which doubles (x2) the number of pulses. Counting both leading and trailing edges
        of both channels (A and B channels) of a quadrature encoder will quadruple (x4) the number of pulses:

          - 1 - count the leading(or trailing) edges from one phase channel.
          - 2 - count the leading and trailing edges from one phase channel.
          - 4 - count both leading and trailing edges of both phase channels.

        The *x124* argument is port specific feature (the mimxrt port uses x124=4 only).

      - *scale*\=value. Sets the scale value. The default value is 1. You may treat scale
        factor as **revolution per pulse**, **angle per pulse** etc.
        Hint: Set scale factor to 1/4 to balance the multiplier x124=4.

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

   Pseudocode is::

    def value(self, value=None):
        _value = self._value
        if value is not None:
            self._value = value
        return _value

.. method:: Encoder.position([value])

   Get (and optional set) the current position of the Encoder as signed integer.
   With no argument the actual position are returned.

   With a single *value* argument the position of Encoder is set to that value.

   Pseudocode is::

    def position(self, position=None):
        _position = self._value * self.scale
        if position is not None:
            self._value = round(position / self.scale)
        return _position

The *scale* parameter allows to get *Encoder.position()* in different units.::

    PPR = 30  # pulses per revolution of the encoder shaft

    enc = Encoder(Pin(0), Pin(1), scale=360 / PPR)  # degreses
    print('degreses', enc.position())

    enc.init(scale=2 * 3.141592 / PPR)              # radians
    print('radians', enc.position())

    enc.init(scale=1 / PPR)                         # rotations
    print('rotations', enc.position())

Simple check of Encoder performance
`encoders_test.py <https://github.com/IhorNehrutsa/MicroPython-quadrature-incremental-encoder/blob/main/encoders_test.py>`_

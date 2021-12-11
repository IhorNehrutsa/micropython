.. currentmodule:: machine
.. _machine.Counter:

class Counter-- Pulse Counter
=============================

This class provides a Pulse Counter service.

Here is described a basics, commons for hardware-counters-based counters of MicroPython ports:

  * :ref:`ESP32.Counter <pcnt.Counter>`
  * mimxrt.Counter - under constructions
  * STM32.Counter - TODO

Minimal example usage::

    from machine import Pin, Counter

    counter = Counter(0, Pin(0, mode=Pin.INPUT))  # create Counter object and start to count input pulses
    counter.init(filter_ns=0)                     # switch filtering off
    value = counter.value()                       # get current Counter value
    value = counter.value(0)                      # get current Counter value, set counter to 0
    counter.deinit()                              # turn off the Counter

    print(counter)                                # show the Counter object properties

Constructor
-----------

.. class:: Counter(id, input=machine.Pin, \*, keyword_arguments)

    Construct and return a new Counter object using the following parameters:

      - *id*. Values of *id* depend on a particular port and its hardware.
        Values 0, 1, etc. are commonly used to select hardware block #0, #1, etc.

      - *input*. The Counter pulses input pin, which is usually a
        :ref:`machine.Pin <machine.Pin>` object, but a port may allow other values,
        like integers or strings, which designate a Pin in the *machine.Pin* class.
        It may be omitted on ports which have predefined pin for *id*-specified hardware block.
        The keyword may be omitted, for example Counter(0, Pin(0)).

    Keyword arguments:

      - *direction*\=value. Specifying the direction of counting. The default value is 1. Suitable values are:

        - if value == 0 or False: count down -1
        - if value != 0 or True: count up +1
        - a :ref:`machine.Pin <machine.Pin>` object. The level at that pin controls
          the counting direction:

            - if Pin.value() == 0: count down -1
            - if Pin.value() == 1: count up +1

      - *filter_ns*\=value. Specifies a ns-value for the minimal time a signal has to be stable
        at the pulse input to be recognized. The largest value is port specific and is the default.
        If the specified value is greater than the largest value, then largest value is used.
        A value of 0 or negative sets the filter is switched off.

Methods
-------

.. method:: Counter.init(keyword_arguments)

   Modify the settings of the Counter object. See the **Constructor** for details about the parameters.

.. method:: Counter.deinit()

   Stops the Counter, disables interrupts and releases hardware resources used by the counter.
   A Soft Reset deinitializes all Counter's objects.

.. method:: Counter.value([value])

   Get (and optional set) the Counter value as signed integer.
   With no argument the actual Counter value are returned.

   With a single *value* argument the Counter is set to that value.

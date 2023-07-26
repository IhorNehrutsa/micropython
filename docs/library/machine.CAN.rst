.. currentmodule:: machine
.. _machine.CAN:

class CAN -- controller area network communication bus
======================================================

CAN implements the standard CAN communications protocol.  At
the physical level it consists of 2 lines: RX and TX.  Note that
to connect the microcontroller to a CAN bus you must use a CAN transceiver
to convert the CAN logic signals from the microcontroller to the correct
voltage levels on the bus.

Example usage (must have transceiver connected)::

   from machine import CAN
   can = CAN(0, tx=4, rx=16, extframe=True, mode=CAN.LOOPBACK, baudrate=500000)
   can.setfilter(0, CAN.FILTER_ADDRESS, [0x102, 0])  # set a filter to receive messages with id = 0x102

	can.send([1,2,3], 123)      # send a message with id 123 and payload b'\x01\x02\x03'
   can.recv()                  # receive message
	can.any()                   # returns True if FIFO is not empty, else False
	can.info()                  # get information about the controller’s error states and TX and RX buffers
	can.deinit()                # turn off the can bus
	can.clear_rx_queue()        # clear messages in the receive buffer
	can.clear_tx_queue()        # clear messages in the transmit buffer


Constructors
------------

.. class:: machine.CAN(bus, ...)

   Construct a CAN object on the given bus(controller). *bus* can be 0 or 1 for STM32 and 0 for ESP32.
   With no additional parameters, the CAN object is created but not
   initialised (it has the settings from the last initialisation of
   the bus, if any).  If extra arguments are given, the bus is initialised.
   See :meth:`CAN.init` for parameters of initialisation.

   The physical pins of the CAN bus can be assigned during init.

Methods
-------

.. method:: CAN.init(bus, *, tx, rx, baudrate, prescaler, mode, extframe=False)

   Initialise the CAN bus with the given parameters:
	 
	  - *bus* ESP32 has only one bus, but still must be defined
     - *mode* is one of:  NORMAL, LOOPBACK, SILENT, SILENT_LOOPBACK
     - if *extframe* is True then the bus uses extended identifiers in the frames
       (29 bits); otherwise it uses standard 11 bit identifiers
     - *baudrate* is used to define a standard speed. Standard speeds are 25000, 50000, 100000, 125000, 250000, 500000, 1000000
     - *tx* defines the gpio used for transmission
     - *rx* defines the gpio used for receiving
     - *bus_off* defines the gpio used for BUS-OFF signal line(optional)
     - *clkout* defines the gpio used for CLKOUT signal line(optional)
     - *tx_queue* defines the number of waiting tx messages can be stored
     - *rx_queue* defines the number of received messages can be stored



.. method:: CAN.deinit()

   Turn off the CAN bus.

.. method:: CAN.restart()

   Force a software restart of the CAN controller without resetting its
   configuration.

   If the controller enters the bus-off state then it will no longer participate
   in bus activity.  If the controller is not configured to automatically restart
   (see :meth:`~CAN.init()`) then this method can be used to trigger a restart,
   and the controller will follow the CAN protocol to leave the bus-off state and
   go into the error active state.

.. method:: CAN.state()

   Return the state of the controller.  The return value can be one of:

   - ``CAN.STOPPED`` -- the controller is completely off and reset;
   - ``CAN.ERROR_ACTIVE`` -- the controller is on and in the Error Active state
     (both TEC and REC are less than 96);
   - ``CAN.BUS_OFF`` -- the controller is on but not participating in bus activity
     (TEC overflowed beyond 255).
   - ``CAN.RECOVERING`` -- the controller is under recover from bus-off state;


.. method:: CAN.info()

   Get information about the controller's error states and TX and RX buffers.
   Returns a dict

   The values in the dict are:

   - state: current state of the bus
   - tx_failed_count: 	number of failed transmissions
   - msgs_to_tx: 		messages in outbox ready to transmit
   - rx_error_counter: 	number of errors on message recieve
   - msgs_to_rx: 		number of messages in outbox
   - arb_lost_count:    number of times controller has lost arbitration
   - rx_missed_count:   number of times inbox has overflowed and message was lost
   - bus_error_count:   number of times there was an error on the bus
   - tx_error_counter:  number of times there was an error on message transmission

.. method:: CAN.setfilter(bank, mode, fifo, params, \*, rtr)

   Configure a filter bank:

   - *bank* is the filter bank that is to be configured (0 for extended, 0 or 1 for standard msg)
   - *mode* is the mode the filter should operate in.
   - *params* is an array of two values that defines the filter.
     The first element will be the id to filter and the second element will be the mask to apply.
     mask bit implementation considers 1 as a don't care state and 0 as a check state.

   +-----------------------+----------------------------------------------+
   | *mode*                | contents of *params* array                   |
   +=======================+==============================================+
   | CAN.FILTER_RAW_SINGLE | *params* will be copied in hardware variable |
   |                       | and single_filter_mode will be selected      |
   |                       | In this mode, *bank* will be ignored         |
   +-----------------------+----------------------------------------------+
   | CAN.FILTER_RAW_DUAL   | *params* will be copied in hardware variable |
   |                       | and single_filter_mode will be cleared       |
   |                       | In this mode, *bank* will be ignored         |
   +-----------------------+----------------------------------------------+
   | CAN.FILTER_ADDRESS    | *params* will be set in hardware registers   |
   |                       | according to *bank* selection                |
   +-----------------------+----------------------------------------------+

   - *rtr* is  bool that states if a filter should accept a remote transmission request message.
     If this argument is not given then it defaults to ``False``.

.. method:: CAN.clearfilter(bank)

   Clear and disables all filters

.. method:: CAN.any(fifo)

   Return ``True`` if any message waiting on the FIFO, else ``False``.

.. method:: CAN.recv(list=None, \*, timeout=5000)

   Receive data on the bus:

     - *list* is an optional list object to be used as the return value
     - *timeout* is the timeout in milliseconds to wait for the receive.

   Return value: A tuple containing four values.

     - The id of the message.
     - A boolean that indicates if the message is an RTR message.
     - Reserved.
     - An array containing the data.

   If *list* is ``None`` then a new tuple will be allocated, as well as a new
   bytes object to contain the data (as the fourth element in the tuple).

   If *list* is not ``None`` then it should be a list object with a least four
   elements.  The fourth element should be a memoryview object which is created
   from either a bytearray or an array of type 'B' or 'b', and this array must
   have enough room for at least 8 bytes.  The list object will then be
   populated with the first three return values above, and the memoryview object
   will be resized inplace to the size of the data and filled in with that data.
   The same list and memoryview objects can be reused in subsequent calls to
   this method, providing a way of receiving data without using the heap.
   For example::

        buf = bytearray(8)
        lst = [0, 0, 0, memoryview(buf)]
        # No heap memory is allocated in the following call
        can.recv(lst, timeout=0)

.. method:: CAN.send(data, id, \*, timeout=0, rtr=False)

   Send a message on the bus:

     - *data* is the data to send (an integer to send, or a buffer object).
     - *id* is the id of the message to be sent.
     - *timeout* is the timeout in milliseconds to wait for the send.
     - *rtr* is a boolean that specifies if the message shall be sent as
       a remote transmission request.  If *rtr* is True then only the length
       of *data* is used to fill in the DLC slot of the frame; the actual
       bytes in *data* are unused.

     If timeout is 0 the message is placed in a buffer and the method returns
     immediately. If all three buffers are in use an exception is thrown.
     If timeout is not 0, the method waits until the message is transmitted.
     If the message can't be transmitted within the specified time an exception
     is thrown.

   Return value: ``None``.

.. method:: CAN.clear_tx_queue()

  Clear all messages from transmitting queue.

.. method:: CAN.clear_rx_queue()

  Clear all messages from receiving queue.


Constants
---------

.. data:: CAN.NORMAL
          CAN.LOOPBACK
          CAN.SILENT
          CAN.SILENT_LOOPBACK
          CAN.LISTEN_ONLY


   The mode of the CAN bus used in :meth:`~CAN.init()`.

   +---------------------+---------------------------------------------+-------+-------+
   | *mode*              | \                                           | STM32 | ESP32 |
   +=====================+=============================================+=======+=======+
   | CAN.NORMAL          | .. image:: img/can_mode_normal.png          |   +   |   +   |
   +---------------------+---------------------------------------------+-------+-------+
   | CAN.LOOPBACK        | .. image:: img/can_mode_loopback.png        |   +   |   +   |
   +---------------------+---------------------------------------------+-------+-------+
   | CAN.SILENT          | .. image:: img/can_mode_silent.png          |   +   |   +   |
   +---------------------+---------------------------------------------+-------+-------+
   | CAN.SILENT_LOOPBACK | .. image:: img/can_mode_silent_loopback.png |   +   |       |
   +---------------------+---------------------------------------------+-------+-------+
   | CAN.LISTEN_ONLY     | .. image:: img/can_mode_listen_only.png     |       |   +   |
   +---------------------+---------------------------------------------+-------+-------+


.. data:: CAN.STOPPED
          CAN.ERROR_ACTIVE
          CAN.BUS_OFF
          CAN.RECOVERING

   Possible states of the CAN controller returned from :meth:`~CAN.state()`.

.. data:: CAN.FILTER_RAW_SINGLE
          CAN.FILTER_RAW_DUAL
          CAN.FILTER_ADDRESS

   The operation mode of a filter used in :meth:`~CAN.setfilter()`.


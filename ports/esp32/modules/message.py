# message.py

class Message:
    def __init__(self, timestamp=0, arbitration_id=0, is_extended_id=True, rtr=0, data=None):
        self._timestamp = timestamp
        self._arbitration_id = arbitration_id
        self._is_extended_id = is_extended_id
        self._rtr = rtr
        self._data = data

    def __repr__(self):
        return f"Message(timestamp={self._timestamp}, arbitration_id={self._arbitration_id}, is_extended_id={self._is_extended_id}, rtr={self._rtr}, data={self._data})"

    @property
    def timestamp(self):
        return self._timestamp

    @timestamp.setter
    def timestamp(self, timestamp):
        self._timestamp = timestamp

    @property
    def arbitration_id(self):
        return self._arbitration_id

    @arbitration_id.setter
    def arbitration_id(self, arbitration_id):
        self._arbitration_id = arbitration_id

    @property
    def is_extended_id(self):
        return self._is_extended_id

    @is_extended_id.setter
    def is_extended_id(self, is_extended_id):
        self._is_extended_id = is_extended_id

    @property
    def rtr(self):
        return self._rtr

    @rtr.setter
    def rtr(self, rtr):
        self._rtr = rtr

    @property
    def data(self):
        return self._data

    @data.setter
    def data(self, data):
        self._data = data

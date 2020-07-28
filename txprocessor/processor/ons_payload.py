import cbor

from sawtooth_sdk.processor.exceptions import InvalidTransaction

class OnsPayload:

    def __init__(self, payload):
        try:
            # The payload is csv utf-8 encoded string
            gsCode = payload["gsCode"]
            action = payload["action"]
            data = payload["data"]
        
        except ValueError:
            raise InvalidTransaction("Invalid payload serialization")

        if not gsCode:
            raise InvalidTransaction('GS1 code is required')

        if '|' in gsCode:
            raise InvalidTransaction('GS1 code cannot contain "|"')

        if not action:
            raise InvalidTransaction('Action is required')

        if action not in ('create', 'update', 'delete'):
            raise InvalidTransaction('Invalid action: {}'.format(action))

        self._gsCode = gsCode
        self._action = action
        self._data = data

    @staticmethod
    def from_bytes(payload):
        return OnsPayload(payload=cbor.loads(payload))

    @property
    def gsCode(self):
        return self._gsCode

    @property
    def action(self):
        return self._action

    @property
    def data(self):
        return self._data
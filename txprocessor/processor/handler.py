from sawtooth_sdk.processor.handler import TransactionHandler
from sawtooth_sdk.processor.exceptions import InvalidTransaction

from ons_payload import OnsPayload
from ons_state import OnsState

class BlockONSTXHandler(TransactionHandler):
    def __init__(self, namespace_prefix):
        self._namespace_prefix = namespace_prefix

    @property
    def family_name(self):
        return 'BlockONSTXHandler'

    @property
    def family_versions(self):
        return ['1.0']

    @property
    def namespaces(self):
        return [self._namespace_prefix]

    def apply(self, transaction, context):
        header = transaction.header
        signer = header.signer_public_key

        ons_payload = OnsPayload.from_bytes(transaction.payload)

        ons_state = OnsState(context)

        if ons_payload.action == 'delete':
            pass
        elif ons_payload.action == 'create':
            pass
        elif ons_payload.action == 'take':
            pass
        else:
            raise InvalidTransaction('Unhandled action: {}'.format(ons_payload.action))
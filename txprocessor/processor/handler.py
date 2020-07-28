from sawtooth_sdk.processor.handler import TransactionHandler
from sawtooth_sdk.processor.exceptions import InvalidTransaction

from ons_payload import OnsPayload
from ons_state import OnsState, Record

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

        if ons_payload.action == 'create':
            if ons_state.get_record(ons_payload.gsCode) is not None:
                raise InvalidTransaction(F'Invalid action: Record already exists: {ons_payload.gsCode}')

            record = Record(gsCode=ons_payload.gsCode, owner_pk=signer, data=ons_payload.data)

            ons_state.set_record(ons_payload.gsCode, record)
            print(F"Record Owner {signer[:6]} created a record.")

        elif ons_payload.action == 'update':
            record = ons_state.get_record(ons_payload.gsCode)

            if record is None:
                raise InvalidTransaction('Invalid action: Update requires an existing record')

            if signer != record.owner_pk:
                raise InvalidTransaction('Invalid action: Record cannot be updated by non-owner')

            record.data = ons_payload.data

            ons_state.set_record(ons_payload.gsCode, record)

            print(F"Record Owner {signer[:6]} updated record: {ons_payload.gsCode} {ons_payload.data}")
        
        elif ons_payload.action == 'delete':
            record = ons_state.get_record(ons_payload.gsCode)

            if record is None:
                raise InvalidTransaction('Invalid action: Record does not exist')

            if signer != record.owner_pk:
                raise InvalidTransaction('Invalid action: Record cannot be deleted by non-owner')

            ons_state.delete_record(ons_payload.gsCode)

            print(F"Record Owner {signer[:6]} deleted record: {ons_payload.gsCode}")
        
        else:
            raise InvalidTransaction('Unhandled action: {}'.format(ons_payload.action))
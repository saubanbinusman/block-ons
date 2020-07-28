import hashlib

from sawtooth_sdk.processor.exceptions import InternalError

ONS_NAMESPACE = "007007"

class Record:
    def __init__(self, gsCode, owner_pk, data):
        self.gsCode = gsCode
        self.owner_pk = owner_pk
        self.data = data


class OnsState:

    TIMEOUT = 3

    def __init__(self, context):
        """Constructor.
        Args:
            context (sawtooth_sdk.processor.context.Context): Access to
                validator state from within the transaction processor.
        """

        self._context = context
        self._address_cache = {}

    def delete_record(self, gsCode):
        """Delete the record with code gsCode from state.
        Args:
            gsCode (str): The code.
        Raises:
            KeyError: The record with gsCode does not exist.
        """

        records = self._load_records(gsCode=gsCode)

        del records[gsCode]
        if records:
            self._store_record(gsCode, records=records)
        else:
            self._delete_record(gsCode)

    def set_record(self, gsCode, record):
        """Store the record in the validator state.
        Args:
            gsCode (str): The code.
            record (Record): The information specifying the current record.
        """

        records = self._load_records(gsCode=gsCode)

        records[gsCode] = record

        self._store_record(gsCode, records=records)

    def get_record(self, gsCode):
        """Get the record associated with gsCode.
        Args:
            gsCode (str): The code.
        Returns:
            (Record): All the information specifying a record.
        """

        return self._load_records(gsCode=gsCode).get(gsCode)

    def _store_record(self, gsCode, records):
        address = self._make_ons_address(gsCode)

        state_data = self._serialize(records)

        self._address_cache[address] = state_data

        self._context.set_state(
            {address: state_data},
            timeout=self.TIMEOUT)

    def _delete_record(self, gsCode):
        address = self._make_ons_address(gsCode)

        self._context.delete_state(
            [address],
            timeout=self.TIMEOUT)

        self._address_cache[address] = None

    def _load_records(self, gsCode):
        address = self._make_ons_address(gsCode)

        if address in self._address_cache:
            if self._address_cache[address]:
                serialized_records = self._address_cache[address]
                records = self._deserialize(serialized_records)
            else:
                records = {}
        else:
            state_entries = self._context.get_state(
                [address],
                timeout=self.TIMEOUT)

            if state_entries:
                self._address_cache[address] = state_entries[0].data
                records = self._deserialize(data=state_entries[0].data)

            else:
                self._address_cache[address] = None
                records = {}

        return records

    def _deserialize(self, data):
        """Take bytes stored in state and deserialize them into Python
        Record objects.
        Args:
            data (bytes): The UTF-8 encoded string stored in state.
        Returns:
            (dict): gsCode (str) keys, Record values.
        """

        records = {}
        try:
            for record in data.decode().split("|"):
                gsCode, owner_pk, data = record.split(",")
                records[gsCode] = Record(gsCode, owner_pk, data)

        except ValueError:
            raise InternalError("Failed to deserialize record data")

        return records

    def _serialize(self, records):
        """Takes a dict of record objects and serializes them into bytes.
        Args:
            records (dict): gsCode (str) keys, Record values.
        Returns:
            (bytes): The UTF-8 encoded string stored in state.
        """

        record_strs = []
        for gsCode, r in records.items():
            record_str = ",".join([gsCode, r.owner_pk, r.data])
            record_strs.append(record_str)

        return "|".join(sorted(record_strs)).encode()

    def _make_ons_address(self, gsCode):
        return ONS_NAMESPACE + hashlib.sha512(gsCode.encode('utf-8')).hexdigest()[:64]

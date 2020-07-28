import os
import cbor

from hashlib import sha512

from sawtooth_signing import create_context
from sawtooth_signing import CryptoFactory

from sawtooth_sdk.protobuf.transaction_pb2 import Transaction
from sawtooth_sdk.protobuf.transaction_pb2 import TransactionHeader

from sawtooth_sdk.protobuf.batch_pb2 import Batch
from sawtooth_sdk.protobuf.batch_pb2 import BatchHeader
from sawtooth_sdk.protobuf.batch_pb2 import BatchList

import urllib.request
from urllib.error import HTTPError

def create_new_user():
    context = create_context('secp256k1')
    private_key = context.new_random_private_key()
    signer = CryptoFactory(context).new_signer(private_key)

    return private_key, signer


def get_payload():
    payload = {
        'Verb': 'set',
        'Name': 'foo',
        'Value': 42
    }

    payload_bytes = cbor.dumps(payload)

    return payload_bytes


def get_batch_list():
    private_key, signer = create_new_user()

    payload_bytes = get_payload()

    # Create TX Header
    txn_header_bytes = TransactionHeader(
        family_name='BlockONSTXHandler',
        family_version='1.0',
        # inputs=['1cf1266e282c41be5e4254d8820772c5518a2c5a8c0c7f7eda19594a7eb539453e1ed7'],
        inputs=[],
        # outputs=['1cf1266e282c41be5e4254d8820772c5518a2c5a8c0c7f7eda19594a7eb539453e1ed7'],
        outputs=[],
        signer_public_key=signer.get_public_key().as_hex(),
        # In this example, we're signing the batch with the same private key,
        # but the batch can be signed by another party, in which case, the
        # public key will need to be associated with that key.
        batcher_public_key=signer.get_public_key().as_hex(),
        # In this example, there are no dependencies.  This list should include
        # an previous transaction header signatures that must be applied for
        # this transaction to successfully commit.
        # For example,
        # dependencies=['540a6803971d1880ec73a96cb97815a95d374cbad5d865925e5aa0432fcf1931539afe10310c122c5eaae15df61236079abbf4f258889359c4d175516934484a'],
        dependencies=[],
        payload_sha512=sha512(payload_bytes).hexdigest()
    ).SerializeToString()

    
    signature = signer.sign(txn_header_bytes)

    # Create TX
    txn = Transaction(
        header=txn_header_bytes,
        header_signature=signature,
        payload=payload_bytes
    )

    # Create Batch Header
    txns = [txn]

    batch_header_bytes = BatchHeader(
        signer_public_key=signer.get_public_key().as_hex(),
        transaction_ids=[txn.header_signature for txn in txns],
    ).SerializeToString()

    # Create Batch
    signature = signer.sign(batch_header_bytes)

    batch = Batch(
        header=batch_header_bytes,
        header_signature=signature,
        transactions=txns
    )
    
    # Create Batch List
    batch_list_bytes = BatchList(batches=[batch]).SerializeToString()

    return batch_list_bytes


def main():
    output = open('intkey.batches', 'wb')
    output.write(get_batch_list())

    # try:
    #     request = urllib.request.Request(
    #         'http://127.0.0.1:8008/batches',
    #         get_batch_list(),
    #         method='POST',
    #         headers={'Content-Type': 'application/octet-stream'})
    #     response = urllib.request.urlopen(request)

    # except HTTPError as e:
    #     response = e.file

main()
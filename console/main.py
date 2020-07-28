import os
import cbor

from hashlib import sha512

from sawtooth_signing import create_context
from sawtooth_signing import CryptoFactory
from sawtooth_signing.secp256k1 import Secp256k1PrivateKey

from sawtooth_sdk.protobuf.transaction_pb2 import Transaction
from sawtooth_sdk.protobuf.transaction_pb2 import TransactionHeader

from sawtooth_sdk.protobuf.batch_pb2 import Batch
from sawtooth_sdk.protobuf.batch_pb2 import BatchHeader
from sawtooth_sdk.protobuf.batch_pb2 import BatchList

import urllib.request
from urllib.error import HTTPError

context = create_context('secp256k1')


def create_user(username):
    with open(F"{username}.priv", "w") as private_key_file:
        private_key_file.write(create_private_key().as_hex())


def get_signer(private_key):
    return CryptoFactory(context).new_signer(private_key)


def create_private_key():
    return context.new_random_private_key()


def to_key_object(private_key_hex):
    return Secp256k1PrivateKey.from_hex(private_key_hex)


def get_payload(gsCode, action, data):
    payload = F"{gsCode},{action},{data}".encode("utf-8")
    return cbor.dumps(payload)


def get_batch_list(private_key):
    signer = get_signer(private_key)

    action = input("Enter action (create, update, delete, exit): ")
    if action not in ("create", "update", "delete", "exit"):
        print("Invalid action.")
        return
    
    if action == "exit":
        exit(0)
    
    gsCode = input("Enter GS-Code: ")
    data = "" if action == "delete" else input("Enter Data: ")
    
    payload_bytes = get_payload(gsCode, action, data)

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
    username = input("Enter username: ")
    filename = F"{username}.priv"

    if not os.path.isfile(filename):
        print("Username does not exist. Login failed!")
        option = input("Do you want to create a new user? (y/n): ")
        
        if option.lower() == "y":
            create_user(username)
        else:
            return
    
    with open(filename, "r") as private_key_file:
        private_key = private_key_file.read()
    
    private_key = to_key_object(private_key)

    while True:
        batch_list = get_batch_list(private_key)

        try:
            request = urllib.request.Request(
                'http://127.0.0.1:8008/batches',
                batch_list,
                method='POST',
                headers={'Content-Type': 'application/octet-stream'})
            response = urllib.request.urlopen(request)
            try:
                print(response.msg)
            except Exception:
                pass
            
            print(response.getcode())

        except HTTPError as e:
            response = e.file
            print(response)

main()
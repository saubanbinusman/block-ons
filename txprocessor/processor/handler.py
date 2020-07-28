from sawtooth_sdk.processor.handler import TransactionHandler

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
        print("HELLLLLLOOOO!!")
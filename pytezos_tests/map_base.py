from pytezos import ContractInterface, pytezos, MichelsonRuntimeError
from unittest import TestCase
from os.path import dirname, join


COLLAB_FN = '../build/tz/contract_proxy_map.tz'
FACTORY_FN = '../build/tz/factory.tz'
SIGN_FN = '../build/tz/sign.tz'


def split_amount(amount, shares, last_address):
    """ Splits amount according to the shares dict """

    total_shares = sum(shares.values())

    # calculating amounts, int always rounds down:
    amounts = {
        address: share * amount // total_shares
        for address, share in shares.items() if address != last_address
    }

    # dust goes to the last_address:
    accumulated_amount = sum(amounts.values())
    amounts[last_address] = amount - accumulated_amount

    # removing 0-operations:
    amounts = {
        address: amount for address, amount in amounts.items()
        if amount > 0
    }

    return amounts
  

class MapBaseCase(TestCase):

    def setUp(self):
        self.collab = ContractInterface.from_file(join(dirname(__file__), COLLAB_FN))
        self.factory = ContractInterface.from_file(join(dirname(__file__), FACTORY_FN))

        # Two core participants:
        self.p1 = 'tz1iQE8ijR5xVPffBUPFubwB9XQJuyD9qsoJ'
        self.p2 = 'tz1MdaJfWzP5pPx3gwPxfdLZTHW6js9havos'

        # One just benefactor:
        self.tips = 'tz1RS9GoEXakf9iyBmSaheLMcakFRtzBXpWE'

        self.admin = self.p1

        self.mint_params = {
            'address': 'KT1VRdyXdMb452GRnSz7tPFQVg96bq2XAmSN',
            'amount': 1,
            'metadata': '697066733a2f2f516d5952724264554578587269473470526679746e666d596b664a4564417157793632683746327771346b517775',
            'royalties': 250
        }

        self.originate_params = {
            self.p1:   {'share': 330, 'isCore': True},
            self.p2:   {'share': 500, 'isCore': True},
            self.tips: {'share': 170, 'isCore': False}
        }

        self.swap_params = {
            'objkt_amount': 1,
            'objkt_id': 30000,
            'xtz_per_objkt': 10_000_000,
        }

        self.factory_init = {
            'originatedContracts': 0,
            'hicetnuncMinterAddress': 'KT1Hkg5qeNhfwpKW4fXvq7HGZB9z2EnmCCA9'
        }

        self.result = None
        self.total_incomings = 0


    def _create_collab(self, sender, params):
        result = self.factory.default(params).interpret(
            storage=self.factory_init, sender=sender)
        self.assertEqual(len(result.operations), 1)

        operation = result.operations[0]
        self.assertTrue(operation['kind'] == 'origination')
        self.collab.storage_from_micheline(operation['script']['storage'])
        self.storage = self.collab.storage()


    def _mint_call(self, sender):
        """ Testing that minting doesn't fail with default params """

        self.result = self.collab.mint_OBJKT(self.mint_params).interpret(
            storage=self.storage, sender=sender)

        self.assertTrue(len(self.result.operations) == 1)
        operation = self.result.operations[0]

        self.assertEqual(operation['parameters']['entrypoint'], 'mint_OBJKT')
        op_bytes = operation['parameters']['value']['args'][1]['bytes']

        metadata = self.mint_params['metadata']
        self.assertEqual(op_bytes, metadata)

        self.assertEqual(operation['destination'],
            self.factory_init['hicetnuncMinterAddress'])
        self.assertEqual(operation['amount'], '0')


    def _swap_call(self, sender):
        """ Testing that swapping doesn't fail with default params """

        self.result = self.collab.swap(self.swap_params).interpret(
            storage=self.storage, sender=sender)

        assert len(self.result.operations) == 1
        assert self.result.operations[0]['parameters']['entrypoint'] == 'swap'


    def _cancel_swap_call(self, sender):
        """ Testing that cancel swap doesn't fail with default params """

        some_swap_id = 42
        self.result = self.collab.cancel_swap(some_swap_id).interpret(
            storage=self.storage, sender=sender)

        assert len(self.result.operations) == 1
        assert self.result.operations[0]['parameters']['entrypoint'] == 'cancel_swap'
        assert self.result.operations[0]['parameters']['value'] == {'int': '42'}


    def _collect_call(self, sender):
        """ Testing that collect doesn't fail with default params """

        some_collect_params = {'objkt_amount': 1, 'swap_id': 42}
        self.result = self.collab.collect(some_collect_params).interpret(
            storage=self.storage, sender=sender)

        assert len(self.result.operations) == 1
        assert self.result.operations[0]['parameters']['entrypoint'] == 'collect'
        assert self.result.operations[0]['parameters']['value']['args'][0] == {'int': '1'}
        assert self.result.operations[0]['parameters']['value']['args'][1] == {'int': '42'}


    def _curate_call(self, sender):
        """ Testing that curate doesn't fail with default params """

        curate_params = {'hDAO_amount': 100, 'objkt_id': 100_000}
        self.result = self.collab.curate(curate_params).interpret(
            storage=self.storage, sender=sender)

        assert len(self.result.operations) == 1
        assert self.result.operations[0]['parameters']['entrypoint'] == 'curate'
        assert self.result.operations[0]['parameters']['value']['args'][0] == {'int': '100'}
        assert self.result.operations[0]['parameters']['value']['args'][1] == {'int': '100000'}


    def _default_call(self, sender, amount):
        """ Testing that distribution in default call works properly """

        self.result = self.collab.default().with_amount(amount).interpret(
            storage=self.storage, sender=sender)

        ops = self.result.operations
        # Operations is collected in reversed order
        # Order means because one (last) operation takes dust:
        ops = list(reversed(ops))

        shares = self.storage['shares']
        last_address = ops[-1]['destination']
        calc_amounts = split_amount(amount, shares, last_address)

        # Checking that sum of the operations is correct and no dust is left
        ops_sum = sum(int(op['amount']) for op in ops)
        self.assertEqual(ops_sum, amount)
        self.assertEqual(len(ops), len(calc_amounts))

        # Checking that each participant get amount he should receive:
        amounts = {op['destination']: int(op['amount']) for op in ops}

        # Check all amounts equals
        self.assertEqual(calc_amounts, amounts)


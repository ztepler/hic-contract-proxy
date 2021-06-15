from pytezos import ContractInterface, pytezos, MichelsonRuntimeError
from unittest import TestCase
from os.path import dirname, join


COLLAB_FN = '../build/tz/contract_proxy_map.tz'
FACTORY_FN = '../build/tz/factory.tz'


class MapInteractionTest(TestCase):

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
            'administrator': self.admin,
            'shares': {
                self.p1: 330,
                self.p2: 500,
                self.tips: 170
            },
            'coreParticipants': {self.p1, self.p2},
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


    def _create_collab(self, sender):
        result = self.factory.default(self.originate_params).interpret(
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

        # TODO: wen operation == 0 it should not appear!
        ops = self.result.operations
        # Operations is collected in reversed order
        # Order means because one (last) operation takes dust:
        ops = list(reversed(ops))

        shares = self.originate_params['shares']
        total_shares = sum(shares.values())
        self.assertEqual(len(ops), len(shares))

        # Checking that sum of the operations is correct and no dust is left
        ops_sum = sum(int(op['amount']) for op in ops)
        self.assertEqual(ops_sum, amount)

        # Checking that each participant get amount he should receive:
        amounts = {op['destination']: int(op['amount']) for op in ops}
        accumulated_amount = 0
        for address, part_amount in amounts.items():
            is_last_operation = address == ops[-1]['destination']
            # Or maybe check that only one operation can diff not more than 1n?
            if is_last_operation:
                calc_amount = amount - accumulated_amount
            else:
                calc_amount = int(shares[address]*amount/total_shares)
            accumulated_amount += calc_amount
            self.assertEqual(calc_amount, part_amount)


    def test_interactions(self):
        # Factory test:
        self._create_collab(self.admin)

        # Test mint call from admin succeed:
        self._mint_call(self.admin)

        # Test mint call without admin role failed:
        with self.assertRaises(MichelsonRuntimeError) as cm:
            self._mint_call(self.p2)
        self.assertTrue('Entrypoint can call only administrator' in str(cm.exception))

        # Test swap call from admin succeed:
        self._swap_call(self.admin)

        # Testing that calling swap from non-administrator address is not possible:
        with self.assertRaises(MichelsonRuntimeError) as cm:
            self._swap_call(self.p2)
        self.assertTrue('Entrypoint can call only administrator' in str(cm.exception))

        # Test cancel swap call from admin succeed:
        self._cancel_swap_call(self.admin)

        # Testing that calling cancel swap from non-administrator address is not possible:
        with self.assertRaises(MichelsonRuntimeError) as cm:
            self._cancel_swap_call(self.tips)
        self.assertTrue('Entrypoint can call only administrator' in str(cm.exception))

        # Test collect call from admin succeed:
        self._collect_call(self.admin)

        # Testing that calling collect from non-administrator address is not possible:
        with self.assertRaises(MichelsonRuntimeError) as cm:
            self._collect_call(self.tips)
        self.assertTrue('Entrypoint can call only administrator' in str(cm.exception))

        # Test curate call from admin succeed:
        self._curate_call(self.admin)

        # Testing that curate call from non-administrator address is not possible:
        with self.assertRaises(MichelsonRuntimeError) as cm:
            self._curate_call(self.tips)
        self.assertTrue('Entrypoint can call only administrator' in str(cm.exception))

        # Default entrypoint tests with value that can be easy splitted:
        self._default_call(self.tips, 1000)

        # Default entrypoint tests with value that hard to split equally:
        self._default_call(self.tips, 337)

        # Default entrypoint tests with value that very hard to split:
        self._default_call(self.tips, 1)

        # TODO: test contract creation from factory with another edgecase params:
        # - test collab with 1 participant cant be created with only 1 share
        # - test that collab with 0 core cant be created
        # - test that maximum participants is limited
        # - 0 share for participant should not be allowed
        # - need to make MORE tests

        # TODO: maybe run this tests with different contracts created with
        # different shares and participant count (starting with factory and
        # then calling all tests)

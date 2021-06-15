from pytezos import ContractInterface, pytezos, MichelsonRuntimeError
from unittest import TestCase
from os.path import dirname, join


CONTRACT_FN = '../build/tz/contract_proxy_map.tz'


class MapInteractionTest(TestCase):

    def setUp(self):
        self.contract = ContractInterface.from_file(join(dirname(__file__), CONTRACT_FN))
        self.p1 = 'tz1iQE8ijR5xVPffBUPFubwB9XQJuyD9qsoJ'
        self.p2 = 'tz1MdaJfWzP5pPx3gwPxfdLZTHW6js9havos'
        self.p3 = 'tz1RS9GoEXakf9iyBmSaheLMcakFRtzBXpWE'

        self.admin = self.p1

        self.mint_params = {
            'address': 'KT1VRdyXdMb452GRnSz7tPFQVg96bq2XAmSN',
            'amount': 1,
            'metadata': '697066733a2f2f516d5952724264554578587269473470526679746e666d596b664a4564417157793632683746327771346b517775',
            'royalties': 250
        }

        self.init_storage = {
            'administrator': self.p1,
            'shares': {
                self.p1: 330,
                self.p2: 500,
                self.p3: 170
            },
            'totalShares': 1000,
            'hicetnuncMinterAddress': 'KT1Hkg5qeNhfwpKW4fXvq7HGZB9z2EnmCCA9',
            'coreParticipants': {self.p1, self.p2, self.p3},
        }

        self.swap_params = {
            'objkt_amount': 1,
            'objkt_id': 30000,
            'xtz_per_objkt': 10_000_000,
        }

        self.result = None
        self.total_incomings = 0


    def _mint_call(self, sender):
        """ Testing that minting doesn't fail with default params """

        self.result = self.contract.mint_OBJKT(self.mint_params).interpret(
            storage=self.init_storage, sender=sender)

        assert len(self.result.operations) == 1
        assert self.result.operations[0]['parameters']['entrypoint'] == 'mint_OBJKT'
        op_bytes = self.result.operations[0]['parameters']['value']['args'][1]['bytes']
        metadata = self.mint_params['metadata']
        assert op_bytes == metadata


    def _swap_call(self, sender):
        """ Testing that swapping doesn't fail with default params """

        self.result = self.contract.swap(self.swap_params).interpret(
            storage=self.init_storage, sender=sender)

        assert len(self.result.operations) == 1
        assert self.result.operations[0]['parameters']['entrypoint'] == 'swap'


    def _cancel_swap_call(self, sender):
        """ Testing that cancel swap doesn't fail with default params """

        some_swap_id = 42
        self.result = self.contract.cancel_swap(some_swap_id).interpret(
            storage=self.init_storage, sender=sender)

        assert len(self.result.operations) == 1
        assert self.result.operations[0]['parameters']['entrypoint'] == 'cancel_swap'
        assert self.result.operations[0]['parameters']['value'] == {'int': '42'}


    def _collect_call(self, sender):
        """ Testing that collect doesn't fail with default params """

        some_collect_params = {'objkt_amount': 1, 'swap_id': 42}
        self.result = self.contract.collect(some_collect_params).interpret(
            storage=self.init_storage, sender=sender)

        assert len(self.result.operations) == 1
        assert self.result.operations[0]['parameters']['entrypoint'] == 'collect'
        assert self.result.operations[0]['parameters']['value']['args'][0] == {'int': '1'}
        assert self.result.operations[0]['parameters']['value']['args'][1] == {'int': '42'}


    def _curate_call(self, sender):
        """ Testing that curate doesn't fail with default params """

        curate_params = {'hDAO_amount': 100, 'objkt_id': 100_000}
        self.result = self.contract.curate(curate_params).interpret(
            storage=self.init_storage, sender=sender)

        assert len(self.result.operations) == 1
        assert self.result.operations[0]['parameters']['entrypoint'] == 'curate'
        assert self.result.operations[0]['parameters']['value']['args'][0] == {'int': '100'}
        assert self.result.operations[0]['parameters']['value']['args'][1] == {'int': '100000'}


    def test_interactions(self):
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
            self._cancel_swap_call(self.p3)
        self.assertTrue('Entrypoint can call only administrator' in str(cm.exception))

        # Test collect call from admin succeed:
        self._collect_call(self.admin)

        # Testing that calling collect from non-administrator address is not possible:
        with self.assertRaises(MichelsonRuntimeError) as cm:
            self._collect_call(self.p3)
        self.assertTrue('Entrypoint can call only administrator' in str(cm.exception))

        # Test curate call from admin succeed:
        self._curate_call(self.admin)

        # Testing that curate call from non-administrator address is not possible:
        with self.assertRaises(MichelsonRuntimeError) as cm:
            self._curate_call(self.p3)
        self.assertTrue('Entrypoint can call only administrator' in str(cm.exception))

        # TODO: default entrypoint tests

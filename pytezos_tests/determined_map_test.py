from pytezos import ContractInterface, pytezos, MichelsonRuntimeError
from unittest import TestCase
from os.path import dirname, join


class DeterminedTest(TestCase):

    def setUp(self):
        self.contract = ContractInterface.from_file(join(dirname(__file__), 'contract_proxy_map.tz'))
        self.p1 = 'tz1iQE8ijR5xVPffBUPFubwB9XQJuyD9qsoJ'
        self.p2 = 'tz1MdaJfWzP5pPx3gwPxfdLZTHW6js9havos'
        self.p3 = 'tz1RS9GoEXakf9iyBmSaheLMcakFRtzBXpWE'

        self.init_storage = {
            'administrator': self.p1,
            'shares': {
                self.p1: 330,
                self.p2: 500,
                self.p3: 170
            },
            'hicetnuncMinterAddress': 'KT1Hkg5qeNhfwpKW4fXvq7HGZB9z2EnmCCA9',
        }

        self.mint_params = {
            'address': 'KT1VRdyXdMb452GRnSz7tPFQVg96bq2XAmSN',
            'amount': 1,
            'metadata': '697066733a2f2f516d5952724264554578587269473470526679746e666d596b664a4564417157793632683746327771346b517775',
            'royalties': 250
        }

        self.swap_params = {
            'objkt_amount': 1,
            'objkt_id': 30000,
            'xtz_per_objkt': 10_000_000,
        }

        self.result = None
        self.total_incomings = 0


    def _mint_call(self):
        """ Testing that minting doesn't fail with default params """

        self.result = self.contract.mint_OBJKT(self.mint_params).interpret(
            storage=self.init_storage, sender=self.p1)

        assert len(self.result.operations) == 1
        assert self.result.operations[0]['parameters']['entrypoint'] == 'mint_OBJKT'


    def _test_mint_call_without_admin_role(self):
        """ Testing that calling mint from non-administrator address is not possible """

        with self.assertRaises(MichelsonRuntimeError):
            self.result = self.contract.mint_OBJKT(self.mint_params).interpret(
                storage=self.result.storage, sender=self.p2)


    def _swap_call(self):
        """ Testing that swapping doesn't fail with default params """

        self.result = self.contract.swap(self.swap_params).interpret(
            storage=self.init_storage, sender=self.p1)

        assert len(self.result.operations) == 1
        assert self.result.operations[0]['parameters']['entrypoint'] == 'swap'


    def _swap_call_without_admin_role(self):
        """ Testing that calling swap from non-administrator address is not possible """

        with self.assertRaises(MichelsonRuntimeError):
            self.result = self.contract.swap(self.swap_params).interpret(
                storage=self.result.storage, sender=self.p2)


    def test_interactions(self):
        self._mint_call()
        self._test_mint_call_without_admin_role()
        self._swap_call()
        self._swap_call_without_admin_role()


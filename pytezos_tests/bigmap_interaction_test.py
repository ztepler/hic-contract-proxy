from pytezos import ContractInterface, pytezos, MichelsonRuntimeError
from unittest import TestCase
from os.path import dirname, join


CONTRACT_FN = '../build/tz/contract_proxy_bigmap.tz'


class BigMapInteractionTest(TestCase):

    def setUp(self):
        self.contract = ContractInterface.from_file(join(dirname(__file__), CONTRACT_FN))
        self.p1 = 'tz1iQE8ijR5xVPffBUPFubwB9XQJuyD9qsoJ'
        self.p2 = 'tz1MdaJfWzP5pPx3gwPxfdLZTHW6js9havos'
        self.p3 = 'tz1RS9GoEXakf9iyBmSaheLMcakFRtzBXpWE'

        self.storage = {
            'administrator': self.p1,
            'accounts': {
                self.p1: {'share': 330, 'withdrawalsSum': 0},
                self.p2: {'share': 500, 'withdrawalsSum': 0},
                self.p3: {'share': 170, 'withdrawalsSum': 0}
            },
            'totalWithdrawalsSum': 0,
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
            storage=self.storage, sender=self.p1)

        assert len(self.result.operations) == 1
        assert self.result.operations[0]['parameters']['entrypoint'] == 'mint_OBJKT'


    def _test_nothing_withdraw_error(self):
        """ Testing that withdrawing with zero balance raises MichelsonRuntimeError """

        with self.assertRaises(MichelsonRuntimeError):
            self.result = self.contract.withdraw().interpret(
                storage=self.result.storage, sender=self.p1, balance=0)


    def _test_mint_call_without_admin_role(self):
        """ Testing that calling mint from non-administrator address is not possible """

        with self.assertRaises(MichelsonRuntimeError):
            self.result = self.contract.mint_OBJKT(self.mint_params).interpret(
                storage=self.result.storage, sender=self.p2)


    def _swap_call(self):
        """ Testing that swapping doesn't fail with default params """

        self.result = self.contract.swap(self.swap_params).interpret(
            storage=self.storage, sender=self.p1)

        assert len(self.result.operations) == 1
        assert self.result.operations[0]['parameters']['entrypoint'] == 'swap'


    def _swap_call_without_admin_role(self):
        """ Testing that calling swap from non-administrator address is not possible """

        with self.assertRaises(MichelsonRuntimeError):
            self.result = self.contract.swap(self.swap_params).interpret(
                storage=self.result.storage, sender=self.p2)


    def _test_p1_withdraw(self):
        """ Testing withdraw from p1 with positive balance """

        self.total_incomings += 10_000_000
        self.result = self.contract.withdraw().interpret(
            storage=self.result.storage, sender=self.p1, balance=self.total_incomings)

        assert len(self.result.operations) == 1
        op = self.result.operations[0]

        assert op['destination'] == self.p1
        assert int(op['amount']) == 3_300_000
        assert self.result.storage['totalWithdrawalsSum'] == 3_300_000

        assert self.result.storage['accounts'][ self.p1 ]['withdrawalsSum'] == 3_300_000
        assert self.result.storage['accounts'][ self.p2 ]['withdrawalsSum'] == 0
        assert self.result.storage['accounts'][ self.p3 ]['withdrawalsSum'] == 0


    def _test_p2_withdraw(self):
        """ Testing withdrawals of p2 without any new incomings """

        self.total_incomings -= 3_300_000

        # testing withdraw from p2 with the balance from prev transaction:
        self.result = self.contract.withdraw().interpret(
            storage=self.result.storage, sender=self.p2, balance=self.total_incomings)

        assert len(self.result.operations) == 1
        op = self.result.operations[0]

        assert op['destination'] == self.p2
        assert int(op['amount']) == 5_000_000
        assert self.result.storage['totalWithdrawalsSum'] == 8_300_000

        assert self.result.storage['accounts'][ self.p1 ]['withdrawalsSum'] == 3_300_000
        assert self.result.storage['accounts'][ self.p2 ]['withdrawalsSum'] == 5_000_000
        assert self.result.storage['accounts'][ self.p3 ]['withdrawalsSum'] == 0


    def _test_p3_withdraw(self):
        """ Testing withdraw from p3 with updated balance """

        # incomings without withdrawal of p2:
        self.total_incomings -= 5_000_000

        # new sales:
        self.total_incomings += 20_000_000

        self.result = self.contract.withdraw().interpret(
            storage=self.result.storage, sender=self.p3, balance=self.total_incomings)

        assert len(self.result.operations) == 1
        op = self.result.operations[0]

        assert op['destination'] == self.p3
        assert int(op['amount']) == 5_100_000
        assert self.result.storage['totalWithdrawalsSum'] == 13_400_000

        assert self.result.storage['accounts'][ self.p1 ]['withdrawalsSum'] == 3_300_000
        assert self.result.storage['accounts'][ self.p2 ]['withdrawalsSum'] == 5_000_000
        assert self.result.storage['accounts'][ self.p3 ]['withdrawalsSum'] == 5_100_000


    def _test_p1_withdraw_again(self):
        """ Again p1 withdraws their part from second sale """

        self.total_incomings -= 5_100_000

        self.result = self.contract.withdraw().interpret(
            storage=self.result.storage, sender=self.p1, balance=self.total_incomings)

        assert len(self.result.operations) == 1
        op = self.result.operations[0]

        assert op['destination'] == self.p1
        assert int(op['amount']) == 6_600_000
        assert self.result.storage['totalWithdrawalsSum'] == 20_000_000

        assert self.result.storage['accounts'][ self.p1 ]['withdrawalsSum'] == 9_900_000
        assert self.result.storage['accounts'][ self.p2 ]['withdrawalsSum'] == 5_000_000
        assert self.result.storage['accounts'][ self.p3 ]['withdrawalsSum'] == 5_100_000


    def test_interactions(self):
        self._mint_call()
        self._test_mint_call_without_admin_role()
        self._test_nothing_withdraw_error()
        self._swap_call()
        self._swap_call_without_admin_role()
        self._test_p1_withdraw()
        self._test_p2_withdraw()
        self._test_p3_withdraw()
        self._test_p1_withdraw_again()


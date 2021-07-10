from sandbox_base import (
    ContractInteractionsBaseTestCase, pkh)


class UnsortedInteractionsTestCase(ContractInteractionsBaseTestCase):

    '''
    def test_withdraw_token(self):
        # Do I need to implement this? Would need to support FA2 only or FA1.2 too?

        # 1. collab mints, then not admin withdraws: failure
        # 2. collab mints, then admin withdraws: success
        # 3. someone mints, then not admin withdraws: failure
        # 4. someone mints, then admin withdraws: success
        # withdraw zero tokens?
        pass
    '''

    '''
    def test_created_contract_params(self):
        pass
        # TODO: test contract created params is equal to expected
        # TODO: test mint/swap/cancel and others?


    def test_reading_views(self):
        pass
        # TODO: test reading views from another contract
    '''

    def test_signature_communications(self):
        pass
        # NEED TO UNDERSTAND WHY THESE LINES ARE FAILING:
        """
        # Creating contract using proxy
        originate_params = {
            pkh(self.p1):   {'share': 330, 'isCore': True},
            pkh(self.p2):   {'share': 500, 'isCore': True},
            pkh(self.tips): {'share': 170, 'isCore': False}
        }

        opg = self.factory.default(originate_params).inject()
        self.bake_block()
        self.collab = self._find_contract_internal_by_hash(self.p1, opg['hash'])

        # TODO: test all signature contract communications
        """
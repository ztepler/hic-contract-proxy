from pytezos import MichelsonRuntimeError
from map_base import MapBaseCase


class SignTest(MapBaseCase):
    def test_views(self):
        sign_kt = 'KT1Hkg5qeNhfwpKW4fXvq7HGZB9z2EnmCCA9'
        entrypoint = 'is_core_participant_callback'

        self._create_collab(self.admin, self.originate_params)

        # p1 is core participant, so result should be True:
        result = self._is_core_participant_call(
            self.p1, sign_callback=sign_kt, sign_entrypoint=entrypoint)
        self.assertTrue(result)

        # tips is not core participant, so result should be False:
        result = self._is_core_participant_call(
            self.tips, sign_callback=sign_kt, sign_entrypoint=entrypoint)
        self.assertFalse(result)

        # minting work:
        self._mint_call(self.admin)

        '''
        # checking that minted hash returned True:
        result = self._is_minted_hash_call(
            self.mint_params['metadata'],
            sign_callback=sign_kt,
            sign_entrypoint=entrypoint)
        self.assertTrue(result)

        # checking that another hash returned False:
        not_minted_metadata = '69420420'
        result = self._is_minted_hash_call(
            not_minted_metadata, sign_callback=sign_kt, sign_entrypoint=entrypoint)
        self.assertFalse(result)
        '''

        # TODO: test is_participant_administrator
        # TODO: test get_total_shares
        # TODO: test get_participant_shares


    ''' WIP:
    def test_signing(self):
        sign_params = {

        }

        self.result = self.sign.sign(sign_params).with_amount(amount).interpret(
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
    '''

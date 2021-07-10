from sandbox_base import (
    ContractInteractionsBaseTestCase, pkh)


class MintInteractionsTestCase(ContractInteractionsBaseTestCase):

    def test_mint_token(self):

        self._originate_default_contract()

        # mint:
        mint_params = {
            'address': self.collab.address,
            'amount': 10,
            'metadata': '697066733a2f2f516d5952724264554578587269473470526679746e666d596b664a4564417157793632683746327771346b517775',
            'royalties': 250
        }

        opg = self.collab.mint_OBJKT(mint_params).inject()
        self.bake_block()
        result = self._find_call_result_by_hash(self.p1, opg['hash'])

        # checking that mint is ok:
        self.assertEqual(self.objkts.storage['all_tokens'](), 1)
        self.assertEqual(self.objkts.storage['ledger'][self.collab.address, 0](), 10)

        # update operators:
        self._add_operator(
            contract=self.collab,
            owner_client=self.p1,
            owner=self.collab.address,
            operator=self.marketplace.address,
            token_id=0)
        self.bake_block()

        # swap:
        swap_params = {
            'objkt_amount': 4,
            'objkt_id': 0,
            'xtz_per_objkt': 1_000_000,
            'creator': self.collab.address,
            'royalties': 250
        }

        swap_id = self.marketplace.storage['counter']()
        opg = self.collab.swap(swap_params).inject()
        self.bake_block()
        result = self._find_call_result_by_hash(self.p1, opg['hash'])

        # collect:
        opg = self.buyer.contract(self.marketplace.address).collect(
            swap_id).with_amount(1_000_000).inject()

        self.bake_block()
        result = self._find_call_result_by_hash(self.p1, opg['hash'])

        # checking objkt holders:
        self.assertEqual(self.objkts.storage['all_tokens'](), 1)
        self.assertEqual(self.objkts.storage['ledger'][self.collab.address, 0](), 6)
        self.assertEqual(self.objkts.storage['ledger'][self.marketplace.address, 0](), 3)
        self.assertEqual(self.objkts.storage['ledger'][pkh(self.buyer), 0](), 1)

        # TODO: checking distribution:
        pass

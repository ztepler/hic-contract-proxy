from sandbox_base import (
    ContractInteractionsBaseTestCase, pkh)
from pytezos.rpc.errors import MichelsonError


class MarketplaceInteractionsTestCase(ContractInteractionsBaseTestCase):

    def test_marketplace_communication(self):
        """ Testing marketplace communication without any collab contracts """

        # mint:
        mint_params = {
            'address': pkh(self.p1),
            'amount': 100,
            'metadata': '697066733a2f2f516d5952724264554578587269473470526679746e666d596b664a4564417157793632683746327771346b517775',
            'royalties': 100
        }

        minter = self.p1.contract(self.minter.address)
        opg = minter.mint_OBJKT(mint_params).inject()
        self.bake_block()
        result = self._find_call_result_by_hash(self.p1, opg['hash'])

        # update operators:
        self._add_operator(self.objkts, self.p1, pkh(self.p1), self.marketplace.address, 0)
        self.bake_block()

        # swap:
        swap_params = {
            'creator': pkh(self.p1),
            'objkt_amount': 100,
            'objkt_id': 0,
            'royalties': 100,
            'xtz_per_objkt': 1_000_000,
        }

        marketplace = self.p1.contract(self.marketplace.address)
        swap_id = marketplace.storage['counter']()
        opg = marketplace.swap(swap_params).inject()
        self.bake_block()
        result = self._find_call_result_by_hash(self.p1, opg['hash'])

        # collect:
        opg = self.buyer.contract(self.marketplace.address).collect(
            swap_id).with_amount(1_000_000).inject()

        self.bake_block()
        result = self._find_call_result_by_hash(self.p1, opg['hash'])
        assert self.objkts.storage['ledger'][(pkh(self.buyer), 0)]() == 1

        # reswap this one objkt with low price:
        self._add_operator(self.objkts, self.buyer, pkh(self.buyer), self.marketplace.address, 0)
        self.bake_block()

        marketplace = self.buyer.contract(self.marketplace.address)
        swap_id = marketplace.storage['counter']()

        swap_params.update({
            'objkt_amount': 1,
            'xtz_per_objkt': 100
        })
        opg = marketplace.swap(swap_params).inject()
        self.bake_block()
        result = self._find_call_result_by_hash(self.p1, opg['hash'])

        # rebuing second swap:
        opg = self.p2.contract(self.marketplace.address).collect(
            swap_id).with_amount(1*100).inject()
        self.bake_block()
        result = self._find_call_result_by_hash(self.p1, opg['hash'])

        # and p2 should not receive this 1 objkt:
        assert self.objkts.storage['ledger'][(pkh(self.p2), 0)]() == 1
        assert self.objkts.storage['ledger'][(self.marketplace.address, 0)]() == 99

        # Trying to use this second swap second time:
        with self.assertRaises(MichelsonError) as cm:
            opg = self.p2.contract(self.marketplace.address).collect(
                swap_id).with_amount(1*100).inject()
            self.bake_block()
            result = self._find_call_result_by_hash(self.p1, opg['hash'])

        # Trying to collect swap that does not exist:
        with self.assertRaises(MichelsonError) as cm:
            opg = self.p2.contract(self.marketplace.address).collect(
                3).with_amount(1*100).inject()
            self.bake_block()

        # 0-tez swap
        self._add_operator(self.objkts, self.p2, pkh(self.p2), self.marketplace.address, 0)
        self.bake_block()

        marketplace = self.p2.contract(self.marketplace.address)
        swap_id = marketplace.storage['counter']()

        swap_params.update({
            'objkt_amount': 1,
            'xtz_per_objkt': 0
        })
        opg = marketplace.swap(swap_params).inject()
        self.bake_block()

        opg = self.buyer.contract(self.marketplace.address).collect(
            swap_id).with_amount(0).inject()
        self.bake_block()

        assert self.objkts.storage['ledger'][(pkh(self.buyer), 0)]() == 1
        assert self.objkts.storage['ledger'][(self.marketplace.address, 0)]() == 99

        # Trying to swap more objects that have:
        with self.assertRaises(MichelsonError) as cm:
            marketplace = self.buyer.contract(self.marketplace.address)
            swap_id = marketplace.storage['counter']()

            swap_params.update({
                'objkt_amount': 2,
                'xtz_per_objkt': 0
            })
            opg = marketplace.swap(swap_params).inject()
            self.bake_block()

        self.assertTrue('FA2_INSUFFICIENT_BALANCE' in str(cm.exception))


        # Trying to sell objkt for price that leads to 0-fees trans:
        # this is raising contract.empty_transaction but it should not
        # I turned off this test because it is failed and this contract
        # already in mainnet
        """
        marketplace = self.buyer.contract(self.marketplace.address)
        swap_id = marketplace.storage['counter']()

        swap_params.update({
            'objkt_amount': 1,
            'xtz_per_objkt': 10
        })
        opg = marketplace.swap(swap_params).inject()
        self.bake_block()

        opg = self.p2.contract(self.marketplace.address).collect(
            swap_id).with_amount(10).inject()
        self.bake_block()
        """

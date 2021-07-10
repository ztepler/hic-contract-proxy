from sandbox_base import (
    ContractInteractionsBaseTestCase, pkh)
from pytezos.rpc.errors import MichelsonError


class LambdaProxyInteractionsTestCase(ContractInteractionsBaseTestCase):

    def test_lambda_proxy(self):

        # Creating contract using proxy
        participants = {
            pkh(self.p1):   {'share': 330, 'isCore': True},
            pkh(self.p2):   {'share': 500, 'isCore': True},
            pkh(self.tips): {'share': 170, 'isCore': False}
        }

        # Packer is just helper contract that converts data to bytes:
        packed_participants = self.packer.pack_originate_hic_proxy(
            participants).interpret().storage.hex()

        originate_params = {
            'templateName': 'hic_proxy',
            'params': packed_participants
        }

        opg = self.factory.create_proxy(originate_params).inject()
        self.bake_block()
        self.collab = self._find_contract_internal_by_hash(self.p1, opg['hash'])

        # Checking that factory have address of new created collab in their ledger:
        metadata = self.factory.storage['originatedContracts'][self.collab.address]()
        self.assertTrue('hic_proxy' in metadata.decode())

        # Calling execute:
        executeParams = {
            'lambda': self.lambdas['hic_mint_OBJKT'],
            'packedParams': '05070707070a00000016013116e679766d18239f246ca78b0a4fdaa637ecf20000a40107070a00000035697066733a2f2f516d5952724264554578587269473470526679746e666d596b664a4564417157793632683746327771346b517775008803'
        }

        opg = self.collab.execute(executeParams).inject()
        self.bake_block()
        result = self._find_call_result_by_hash(self.p1, opg['hash'])

        # Checking result params:
        self.assertTrue(len(result.operations) == 1)
        op = result.operations[0]
        self.assertEqual(op['destination'], self.minter.address)
        self.assertTrue(op['amount'] == '0')
        self.assertTrue(op['parameters']['entrypoint'] == 'mint_OBJKT')

        # Creating another one collab with the same params:
        originate_params = {
            'templateName': 'hic_proxy',
            'params': packed_participants
        }

        opg = self.factory.create_proxy(originate_params).inject()
        self.bake_block()

        # Checking that basic proxy created:
        participants = {
            pkh(self.p1): 330,
            pkh(self.p2): 670}

        packed_participants = self.packer.pack_originate_basic_proxy(
            participants).interpret().storage.hex()

        originate_params = {
            'templateName': 'basic_proxy',
            'params': packed_participants
        }

        opg = self.factory.create_proxy(originate_params).inject()
        self.bake_block()

        # Trying to originate contract with name that does not exist failed:
        originate_params = {
            'templateName': 'unknown',
            'params': packed_participants
        }

        with self.assertRaises(MichelsonError) as cm:
            opg = self.factory.create_proxy(originate_params).inject()
            self.bake_block()
        self.assertTrue("Template is not found" in str(cm.exception))

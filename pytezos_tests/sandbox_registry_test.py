from sandbox_base import (
    ContractInteractionsBaseTestCase, pkh, str_to_hex_bytes)


class RegistryInteractionsTestCase(ContractInteractionsBaseTestCase):

    def test_registry_communication(self):

        self._originate_default_contract()

        # Registry test:
        metadata = str_to_hex_bytes(
            'ipfs://QmVJzbVtq1sc8Cj2ZJFJmSBZVWfLDvsL3asuimUBvMARiB')
        subjkt = str_to_hex_bytes('MEGA COLLABA')

        registry_params = {
            'metadata': metadata,
            'subjkt': subjkt
        }

        opg = self.collab.registry(registry_params).inject()
        self.bake_block()
        result = self._find_call_result_by_hash(self.p1, opg['hash'])
        self.assertEqual(len(result.operations), 1)
        op = result.operations[0]
        self.assertEqual(op['destination'], self.registry.address)
        self.assertEqual(op['parameters']['entrypoint'], 'registry')

        self.assertTrue(self.registry.storage['subjkts'][subjkt])
        self.assertTrue(self.registry.storage['entries'][self.collab.address])
        self.assertEqual(
            self.registry.storage['registries'][self.collab.address](),
            subjkt)
        self.assertEqual(
            self.registry.storage['subjkts_metadata'][subjkt](),
            metadata)

        # Unregistry test:
        opg = self.collab.unregistry().inject()
        self.bake_block()
        result = self._find_call_result_by_hash(self.p1, opg['hash'])

        op = result.operations[0]
        self.assertEqual(op['destination'], self.registry.address)
        self.assertEqual(op['parameters']['entrypoint'], 'unregistry')


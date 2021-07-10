from pytezos import MichelsonRuntimeError
from hic_base import HicBaseCase


class FactoryTest(HicBaseCase):
    def test_factory(self):
        random_address = 'KT1Hkg5qeNhfwpKW4fXvq7HGZB9z2EnmCCA9'
        entrypoint = 'not_existed_entrypoint'

        # Anyone can create collab
        self._create_collab(self.p2, self.originate_params)
        contract_address = list(
            self.factory_storage['originatedContracts'].keys())[0]

        # Checking view is contract originated, result should be True:
        result = self._is_originated_contract(
            contract_address, sign_callback=random_address, sign_entrypoint=entrypoint)
        self.assertTrue(result)

        # Checking view for random contract, should be False:
        result = self._is_originated_contract(
            random_address, sign_callback=random_address, sign_entrypoint=entrypoint)
        self.assertFalse(result)

        # Trying to add template from not admin address:
        with self.assertRaises(MichelsonRuntimeError) as cm:
            self._add_template(self.p2)
        self.assertTrue('Entrypoint can call only administrator' in str(cm.exception))

        # Trying to add template from admin address:
        self._add_template(self.admin)

        # Trying to remove template from not admin address:
        with self.assertRaises(MichelsonRuntimeError) as cm:
            self._remove_template(self.p2)
        self.assertTrue('Entrypoint can call only administrator' in str(cm.exception))

        # Trying to remove template from admin address:
        self._remove_template(self.admin)

        # Checking that removed template is not possible to use:
        with self.assertRaises(MichelsonRuntimeError) as cm:
            self._create_collab(self.p2, self.originate_params, contract='added_template')
        self.assertTrue('Template is not found' in str(cm.exception))

        # Trying to update admin from not admin address:
        with self.assertRaises(MichelsonRuntimeError) as cm:
            self._factory_update_admin(self.p2, self.tips)
        self.assertTrue('Entrypoint can call only administrator' in str(cm.exception))

        # Trying to accept admin rights before transfer:
        with self.assertRaises(MichelsonRuntimeError) as cm:
            self._factory_accept_ownership(self.tips)
        self.assertTrue('Not proposed admin' in str(cm.exception))

        # Trying to update admin admin address:
        self._factory_update_admin(self.admin, self.tips)

        # Checking that another address can't accept:
        with self.assertRaises(MichelsonRuntimeError) as cm:
            self._factory_accept_ownership(self.p2)
        self.assertTrue('Not proposed admin' in str(cm.exception))

        # Checking that proposed can accept:
        self._factory_accept_ownership(self.tips)

        # Trying to add template new admin address:
        self._add_template(self.tips)

        # Checking that entrypoints is not allow to send any tez:
        calls = [
            lambda: self._create_collab(self.p1, self.originate_params, amount=100),
            lambda: self._add_template(self.tips, amount=100),
            lambda: self._remove_template(self.tips, amount=100),
            lambda: self._is_originated_contract(
                random_address, random_address, entrypoint, amount=100),
            lambda: self._factory_update_admin(self.tips, self.p2, amount=100),
            lambda: self._factory_accept_ownership(self.p1, amount=100)
        ]

        for call in calls:
            with self.assertRaises(MichelsonRuntimeError) as cm:
                call()
            self.assertTrue('This entrypoint should not receive tez' in str(cm.exception))

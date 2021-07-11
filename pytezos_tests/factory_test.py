from pytezos import MichelsonRuntimeError
from hic_base import HicBaseCase


class FactoryTest(HicBaseCase):

    def _test_admin_change(self):

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


    def _test_no_tez_entrypoints(self):

        # Checking that entrypoints is not allow to send any tez:
        calls = [
            lambda: self._factory_create_proxy(self.p1, self.originate_params, amount=100),
            lambda: self._factory_add_template(self.tips, amount=100),
            lambda: self._factory_remove_template(self.tips, amount=100),
            lambda: self._factory_is_originated_contract(amount=100),
            lambda: self._factory_update_admin(self.tips, self.p2, amount=100),
            lambda: self._factory_accept_ownership(self.p1, amount=100),
            lambda: self._factory_add_record(self.p1, amount=100),
            lambda: self._factory_remove_record(self.p1, amount=100)
        ]

        for call in calls:
            with self.assertRaises(MichelsonRuntimeError) as cm:
                call()
            self.assertTrue('This entrypoint should not receive tez' in str(cm.exception))


    def _test_no_admin_rights(self):
        """ Tests that call to all admin entrypoints failed for not admin user """

        not_admin = self.p2
        admin_calls = [
            lambda: self._factory_add_template(not_admin),
            lambda: self._factory_remove_template(not_admin),
            lambda: self._factory_update_admin(not_admin, self.p2),
            lambda: self._factory_add_record(not_admin),
            lambda: self._factory_remove_record(not_admin)
        ]

        for call in admin_calls:
            with self.assertRaises(MichelsonRuntimeError) as cm:
                call()
            self.assertTrue('Entrypoint can call only administrator' in str(cm.exception))


    def _test_records(self):
        # removing all records from factory:
        self.factory_storage['records'] = {}

        # no records added, trying to originate proxy
        # and failwith "Record is not found":
        with self.assertRaises(MichelsonRuntimeError) as cm:
            self._factory_create_proxy(self.p1, self.originate_params)
        self.assertTrue('Record is not found' in str(cm.exception))

        # adding all records is succeeded:
        for name, address in self.addresses.items():
            self._factory_add_record(
                self.admin, name, self._pack_address(address))

        # contract origination is succeeded:
        self._factory_create_proxy(self.p1, self.originate_params)

        # checking contract addresses:
        for name, address in self.addresses.items():
            self.assertEqual(self.collab_storage[name], address)

        # removing one of the records succeeded:
        self._factory_remove_record(self.admin, 'minterAddress')

        # adding record with nat type instead of address is succeed:
        self._factory_add_record(
            self.admin, 'minterAddress', self._pack_nat(42))

        # contract origination failed: "Unpack failed"
        with self.assertRaises(MichelsonRuntimeError) as cm:
            self._factory_create_proxy(self.p1, self.originate_params)
        self.assertTrue('Unpack failed' in str(cm.exception))

        # replacing record with this name with correct address:
        self._factory_add_record(
            self.admin,
            'minterAddress',
            self._pack_address(self.addresses['minterAddress']))

        # contract origination succeeded:
        self._factory_create_proxy(self.p1, self.originate_params)


    def test_factory(self):
        random_address = 'KT1Hkg5qeNhfwpKW4fXvq7HGZB9z2EnmCCA9'
        entrypoint = 'not_existed_entrypoint'

        # Testing records before any interactions:
        self._test_records()

        # Anyone can create collab
        self._factory_create_proxy(self.p2, self.originate_params)
        contract_address = list(
            self.factory_storage['originatedContracts'].keys())[0]

        # Checking view is contract originated, result should be True:
        result = self._factory_is_originated_contract(
            contract_address, callback=random_address, entrypoint=entrypoint)
        self.assertTrue(result)

        # Checking view for random contract, should be False:
        result = self._factory_is_originated_contract(
            random_address, callback=random_address, entrypoint=entrypoint)
        self.assertFalse(result)

        # Trying to add template from not admin address:
        with self.assertRaises(MichelsonRuntimeError) as cm:
            self._factory_add_template(self.p2)
        self.assertTrue('Entrypoint can call only administrator' in str(cm.exception))

        # Trying to add template from admin address:
        self._factory_add_template(self.admin)

        # Trying to remove template from not admin address:
        with self.assertRaises(MichelsonRuntimeError) as cm:
            self._factory_remove_template(self.p2)
        self.assertTrue('Entrypoint can call only administrator' in str(cm.exception))

        # Trying to remove template from admin address:
        self._factory_remove_template(self.admin)

        # Checking that removed template is not possible to use:
        with self.assertRaises(MichelsonRuntimeError) as cm:
            self._factory_create_proxy(self.p2, self.originate_params, contract='added_template')
        self.assertTrue('Template is not found' in str(cm.exception))

        # Running tests that in result changes admin to self.tips:
        self._test_admin_change()

        # Trying to add template new admin address:
        self._factory_add_template(self.tips)

        self._test_no_tez_entrypoints()
        self._test_no_admin_rights()

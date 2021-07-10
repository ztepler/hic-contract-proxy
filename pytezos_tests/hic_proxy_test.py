from pytezos import MichelsonRuntimeError
from hic_base import HicBaseCase


class MapInteractionTest(HicBaseCase):

    def _test_admin_change(self):
        """ This is copy of the tests that made for factory, I just changed
            entrypoints. Decided that it is better to copy than
            make it abstract """

        # Trying to update admin from not admin address:
        with self.assertRaises(MichelsonRuntimeError) as cm:
            self._collab_update_admin(self.p2, self.tips)
        self.assertTrue('Entrypoint can call only administrator' in str(cm.exception))

        # Trying to accept admin rights before transfer:
        with self.assertRaises(MichelsonRuntimeError) as cm:
            self._collab_accept_ownership(self.tips)
        self.assertTrue('Not proposed admin' in str(cm.exception))

        # Trying to update admin admin address:
        self._collab_update_admin(self.admin, self.tips)

        # Checking that another address can't accept:
        with self.assertRaises(MichelsonRuntimeError) as cm:
            self._collab_accept_ownership(self.p2)
        self.assertTrue('Not proposed admin' in str(cm.exception))

        # Checking that proposed can accept:
        self._collab_accept_ownership(self.tips)


    def _test_no_tez_entrypoints(self):
        # Checking that entrypoints is not allow to send any tez:
        calls = [
            lambda: self._collab_mint(self.admin, amount=100),
            lambda: self._collab_swap(self.admin, amount=100),
            lambda: self._collab_cancel_swap(self.admin, amount=100),
            lambda: self._collab_collect(self.admin, amount=100),
            lambda: self._collab_curate(self.admin, amount=100),
            lambda: self._collab_registry(self.admin, amount=100),
            lambda: self._collab_unregistry(self.admin, amount=100),
            lambda: self._collab_is_core_participant(self.admin, amount=100),
            lambda: self._collab_update_operators(self.admin, amount=100),
            lambda: self._collab_is_administrator(self.admin, amount=100),
            lambda: self._collab_get_total_shares(amount=100),
            lambda: self._collab_get_participant_shares(self.admin, amount=100),
            lambda: self._collab_update_admin(self.admin, self.p2, amount=100),
            lambda: self._collab_accept_ownership(self.admin, amount=100),
            # lambda: self._collab_trigger_pause(self.admin, amount=100),
        ]

        for call in calls:
            with self.assertRaises(MichelsonRuntimeError) as cm:
                call()
            self.assertTrue('This entrypoint should not receive tez' in str(cm.exception))


    def _test_no_admin_rights(self):
        """ Tests that call to all admin entrypoints failed for not admin user """
        # TODO: make list of all admin entries with lambdas

        not_admin = self.p2
        admin_calls = [
            lambda: self._collab_mint(not_admin),
            lambda: self._collab_swap(not_admin),
            lambda: self._collab_cancel_swap(not_admin),
            lambda: self._collab_collect(not_admin),
            lambda: self._collab_curate(not_admin),
            lambda: self._collab_registry(not_admin),
            lambda: self._collab_unregistry(not_admin),
            lambda: self._collab_update_operators(not_admin),
            lambda: self._collab_update_admin(not_admin, self.tips),
            # lambda: self._collab_trigger_pause(not_admin),
            # lambda: self._collab_execute(not_admin),
        ]

        for call in admin_calls:
            with self.assertRaises(MichelsonRuntimeError) as cm:
                call()
            self.assertTrue('Entrypoint can call only administrator' in str(cm.exception))


    def _test_views(self):

        # is_core_participant test, True case:
        result = self._collab_is_core_participant(self.p1)
        self.assertTrue(result)

        # is_core_participant test, False case:
        result = self._collab_is_core_participant(self.tips)
        self.assertFalse(result)

        # is_administrator test, True case:
        result = self._collab_is_administrator(self.admin)
        self.assertTrue(result)

        # is_administrator test, False case:
        result = self._collab_is_administrator(self.tips)
        self.assertFalse(result)

        # get_total_shares test:
        result = self._collab_get_total_shares()
        self.assertEqual(result, self.collab_storage['totalShares'])

        # get_participant_shares test:
        result = self._collab_get_participant_shares(self.p1)
        participantShares = self.collab_storage['shares'].get(self.p1, 0)
        self.assertEqual(result, participantShares)


    def test_interactions(self):
        # Factory test:
        self._factory_create_proxy(self.admin, self.originate_params)

        # Running views test before any contract updates:
        self._test_views()

        # Checking that not admin fails to run admin entrypoints:
        self._test_no_admin_rights()

        # Test mint call from admin succeed:
        self._collab_mint(self.admin)

        # Test mint call without admin role failed:
        with self.assertRaises(MichelsonRuntimeError) as cm:
            self._collab_mint(self.p2)
        self.assertTrue('Entrypoint can call only administrator' in str(cm.exception))

        # Test swap call from admin succeed:
        self._collab_swap(self.admin)

        # Testing that calling swap from non-administrator address is not possible:
        with self.assertRaises(MichelsonRuntimeError) as cm:
            self._collab_swap(self.p2)
        self.assertTrue('Entrypoint can call only administrator' in str(cm.exception))

        # Test cancel swap call from admin succeed:
        self._collab_cancel_swap(self.admin)

        # Testing that calling cancel swap from non-administrator address is not possible:
        with self.assertRaises(MichelsonRuntimeError) as cm:
            self._collab_cancel_swap(self.tips)
        self.assertTrue('Entrypoint can call only administrator' in str(cm.exception))

        # Test collect call from admin succeed:
        self._collab_collect(self.admin)

        # Testing that calling collect from non-administrator address is not possible:
        with self.assertRaises(MichelsonRuntimeError) as cm:
            self._collab_collect(self.tips)
        self.assertTrue('Entrypoint can call only administrator' in str(cm.exception))

        # Test curate call from admin succeed:
        self._collab_curate(self.admin)

        # Testing that curate call from non-administrator address is not possible:
        with self.assertRaises(MichelsonRuntimeError) as cm:
            self._collab_curate(self.tips)
        self.assertTrue('Entrypoint can call only administrator' in str(cm.exception))

        # Default entrypoint tests with value that can be easy splitted:
        self._collab_default(self.tips, 1000)

        # Default entrypoint tests with value that hard to split equally:
        self._collab_default(self.tips, 337)

        # Default entrypoint tests with value that very hard to split:
        self._collab_default(self.tips, 1)

        # Default entrypoint tests with very big value (100 bln tez):
        self._collab_default(self.tips, 10**17)

        # Collab with very crazy big shares:
        crazy_params = {
            self.p1: {'share': 10**35, 'isCore': True},
            self.p2: {'share': 10**35, 'isCore': True},
            self.tips: {'share': 10**35, 'isCore': True}
        }

        self._factory_create_proxy(self.p2, crazy_params)
        self._collab_default(self.tips, 10**17)

        # Mint from admin address (now admin is p2):
        self._collab_mint(self.p2)
        with self.assertRaises(MichelsonRuntimeError) as cm:
            self._collab_mint(self.admin)
        self.assertTrue('Entrypoint can call only administrator' in str(cm.exception))

        # Collab with 1 participant can be created with only 1 share,
        # and we allow to have participants with 0 share (why not?):
        single = {
            self.p1: {'share': 1, 'isCore': True},
            self.p2: {'share': 0, 'isCore': True},
        }
        self._factory_create_proxy(self.admin, single)
        self._collab_default(self.tips, 1000)

        # Collab can't be created with only 0 shares:
        with self.assertRaises(MichelsonRuntimeError) as cm:
            twin = {
                self.p1: {'share': 0, 'isCore': True},
                self.p2: {'share': 0, 'isCore': True},
            }
            self._factory_create_proxy(self.admin, twin)
        msg = 'Sum of the shares should be more than 0n'
        self.assertTrue(msg in str(cm.exception))

        # Collab with zero-core can't be created:
        with self.assertRaises(MichelsonRuntimeError) as cm:
            no_core = {
                self.p1: {'share': 1, 'isCore': False},
                self.p2: {'share': 1, 'isCore': False},
            }
            self._factory_create_proxy(self.admin, no_core)
        msg = 'Collab contract should have at least one core'
        self.assertTrue(msg in str(cm.exception))

        self._test_no_tez_entrypoints()

        # Running views again for collab with 1 participant:
        self._test_views()

        # Running update operatiors from admin check:
        self._collab_update_operators(self.admin)

        # TODO: test that only admin can call:
        # - registry
        # - unregistry
        # - execute lambda call
        # - update_operators
        # - trigger_pause

        # TODO: make separate method to test all lambdas

        # Running tests that in result changes admin to self.tips:
        self._test_admin_change()

        # checking that self.tips can mint now:
        self._collab_mint(self.tips)

        # checking view returns true now::
        result = self._collab_is_administrator(self.tips)
        self.assertTrue(result)

        # TODO: Collab with too many participants can't be created:
        # TODO: NEED TO TEST LIMIT
        # TODO: need to make MORE tests

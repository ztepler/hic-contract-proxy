from pytezos import MichelsonRuntimeError
from hic_base import HicBaseCase
from pytezos.crypto.key import Key


# TODO: should I split this test into separate ones?

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
            lambda: self._collab_trigger_pause(self.admin, amount=100),
        ]

        for call in calls:
            with self.assertRaises(MichelsonRuntimeError) as cm:
                call()
            self.assertTrue('This entrypoint should not receive tez' in str(cm.exception))


    def _test_no_admin_rights(self):
        """ Tests that call to all admin entrypoints failed for not admin user """

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
            lambda: self._collab_trigger_pause(not_admin),
            lambda: self._collab_execute(not_admin),
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


    def _test_pause(self):

        # Checking pause:
        self._collab_trigger_pause(self.admin)

        # These calls should fail when pause:
        paused_calls = [
            lambda: self._collab_mint(self.admin),
            lambda: self._collab_swap(self.admin),
            lambda: self._collab_cancel_swap(self.admin),
            lambda: self._collab_collect(self.admin),
            lambda: self._collab_curate(self.admin),
            lambda: self._collab_registry(self.admin),
            lambda: self._collab_unregistry(self.admin),
            lambda: self._collab_update_operators(self.admin),
            lambda: self._collab_execute(self.admin),
        ]

        for call in paused_calls:
            with self.assertRaises(MichelsonRuntimeError) as cm:
                call()
            self.assertTrue('Contract is paused' in str(cm.exception))

        # Unpausing collab:
        self._collab_trigger_pause(self.admin)


    def _test_lambdas(self):
        """ Testing that lambda calls emits transactions that goes to right
            direction
        """

        destinations = {
            'mint_OBJKT': self.collab.storage['minterAddress']()
        }

        for entrypoint_name, destination in destinations.items():
            execute_params = self._prepare_lambda_params(entrypoint_name)
            result = self._collab_execute(self.admin, params=execute_params)
            self.assertTrue(len(result.operations) == 1)
            op = result.operations[0]
            self.assertTrue(op['destination'] == destination)
            self.assertTrue(op['parameters']['entrypoint'] == entrypoint_name)


    def test_interactions(self):

        # Factory test:
        self._factory_create_proxy(self.admin, self.originate_params)

        # Checking how pause works:
        self._test_pause()

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

        # TODO: remove duplicated tests:
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

        # Collab with very big share sums (10**12 is hard limit):
        crazy_params = {
            self.p1: {'share': 10**11, 'isCore': True},
            self.p2: {'share': 10**11, 'isCore': True},
            self.tips: {'share': 10**11, 'isCore': True}
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

        self._test_no_tez_entrypoints()

        # Running views again for collab with 1 participant:
        self._test_views()

        # Running update operatiors from admin check:
        self._collab_update_operators(self.admin)

        # Running tests that in result changes admin to self.tips:
        self._test_admin_change()

        # checking that self.tips can mint now:
        self._collab_mint(self.tips)

        # checking view returns true now::
        result = self._collab_is_administrator(self.tips)
        self.assertTrue(result)

        # returning admin back:
        self._collab_update_admin(self.tips, self.admin)
        self._collab_accept_ownership(self.admin)

        # running lambda testing:
        self._test_lambdas()


    def test_zero_core_participants_one(self):
        """ Zero core participants should be possible """

        originate_params = {
            self.p1:   {'share': 330, 'isCore': False},
            self.p2:   {'share': 500, 'isCore': False},
            self.tips: {'share': 170, 'isCore': False}
        }

        self._factory_create_proxy(self.p2, originate_params)


    def test_zero_core_participants_two(self):
        """ Zero core participants should be possible """

        originate_params = {
            self.tips: {'share': 170, 'isCore': False}
        }

        self._factory_create_proxy(self.p2, originate_params)


    def test_no_participants(self):
        """ No participants should not be allowed """

        originate_params = {}

        with self.assertRaises(MichelsonRuntimeError) as cm:
            self._factory_create_proxy(self.p2, originate_params)
        # There are no special msg, 0 shares should be failwithed


    def test_too_many_participants(self):
        """ More than 108 participants is not allowed """

        COUNT = 109

        originate_params = {
            Key.generate(export=False).public_key_hash(): {
                'share': 170,
                'isCore': False
            } for _ in range(COUNT)
        }

        with self.assertRaises(MichelsonRuntimeError) as cm:
            self._factory_create_proxy(self.p2, originate_params)
        msg = 'The maximum participants count is 108'
        self.assertTrue(msg in str(cm.exception))


    def test_too_many_shares(self):
        """ More than 10**12 shares is not allowed """

        originate_params = {
            self.p1:   {'share': 10**12, 'isCore': False},
            self.p2:   {'share': 10**12, 'isCore': False},
        }

        with self.assertRaises(MichelsonRuntimeError) as cm:
            self._factory_create_proxy(self.p2, originate_params)
        msg = 'The maximum shares is 10**12'
        self.assertTrue(msg in str(cm.exception))


    def test_hangzhou_views(self):
        shares = {self.p1: 420, self.p2: 69}
        core_participants = [self.p1]
        administrator = self.p2

        originate_params = {
            address: {'share': share, 'isCore': address in core_participants}
            for address, share in shares.items()
        }

        self._factory_create_proxy(administrator, originate_params)

        self.assertEqual(administrator, self._collab_get_administrator())
        self.assertEqual(shares, self._collab_get_shares())
        self.assertEqual(core_participants, self._collab_get_core_participants())


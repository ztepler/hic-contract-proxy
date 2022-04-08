from pytezos import MichelsonRuntimeError, pytezos
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
            lambda: self._collab_registry(self.admin, amount=100),
            lambda: self._collab_unregistry(self.admin, amount=100),
            lambda: self._collab_update_operators(self.admin, amount=100),
            lambda: self._collab_update_admin(self.admin, self.p2, amount=100),
            lambda: self._collab_accept_ownership(self.admin, amount=100),
            lambda: self._collab_set_threshold(self.admin, amount=100),
            lambda: self._collab_withdraw(self.admin, amount=100),
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
            lambda: self._collab_registry(not_admin),
            lambda: self._collab_unregistry(not_admin),
            lambda: self._collab_update_operators(not_admin),
            lambda: self._collab_update_admin(not_admin, self.tips),
            lambda: self._collab_execute(not_admin),
            lambda: self._collab_set_threshold(not_admin),
        ]

        for call in admin_calls:
            with self.assertRaises(MichelsonRuntimeError) as cm:
                call()
            self.assertTrue('Entrypoint can call only administrator' in str(cm.exception))


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

        # Running update operatiors from admin check:
        self._collab_update_operators(self.admin)

        # Running tests that in result changes admin to self.tips:
        self._test_admin_change()

        # checking that self.tips can mint now:
        self._collab_mint(self.tips)

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

        self.assertEqual(0, self._collab_get_total_received())
        self._collab_default(self.p1, 108)
        self.assertEqual(108, self._collab_get_total_received())
        self._collab_default(self.p1, 42)
        self.assertEqual(150, self._collab_get_total_received())


    def test_should_redistribute_with_given_threshold(self):
        def calc_undistributed_sum():
            return sum(self.collab_storage['undistributed'].values())

        originate_params = {
            self.p1:   {'share': 1, 'isCore': True},
            self.p2:   {'share': 1, 'isCore': True},
        }

        self._factory_create_proxy(self.admin, originate_params)

        # setting threshold for 1xtz:
        self._collab_set_threshold(self.admin, threshold=1_000_000)

        # first time it should not be distributed because 0.5xtz < 1xtz
        self._collab_default(self.p1, amount=1_000_000)
        self.assertEqual(calc_undistributed_sum(), 1_000_000)

        # second time it should redistribute all funds
        self._collab_default(self.p1, amount=1_000_000)
        self.assertEqual(calc_undistributed_sum(), 0)

        # third time with the same threshold should be enough too:
        self._collab_default(self.p1, amount=2_000_000)
        self.assertEqual(calc_undistributed_sum(), 0)

        # the same amount with new threshold shold not be distributed:
        self._collab_set_threshold(self.admin, threshold=3_000_000)
        self._collab_default(self.p1, amount=2_000_000)
        self.assertEqual(calc_undistributed_sum(), 2_000_000)

        self._collab_default(self.p1, amount=2_000_000)
        self.assertEqual(calc_undistributed_sum(), 4_000_000)

        # checking that withdraw works:
        amount = self._collab_withdraw(self.p1, recipient=self.p2)
        self.assertEqual(amount, 2_000_000)
        self.assertEqual(calc_undistributed_sum(), 2_000_000)

        # withdraw second time should fail:
        amount = self._collab_withdraw(self.p1, recipient=self.p2)
        self.assertEqual(amount, 0)

        # and then auto-distribution should work:
        self._collab_default(self.p1, amount=10_000_000)
        self.assertEqual(calc_undistributed_sum(), 0)


    def test_should_aggregate_residuals_and_then_redistribute_them(self):
        def generate_key():
            return pytezos.key.generate(export=False).public_key_hash()

        originate_params = {
            generate_key(): {'share': 1, 'isCore': True}
            for _ in range(42)
        }

        self._factory_create_proxy(self.admin, originate_params)

        # in the following case 42 should be distributed and 41 will kept as
        # residuals:
        self._collab_default(self.p1, amount=83)
        self.assertEqual(self.collab_storage['residuals'], 41)

        # then only 1 mutez required to redistribute all:
        self._collab_default(self.p1, amount=1)
        self.assertEqual(self.collab_storage['residuals'], 0)

        # checking scenario with accumulation:
        self._collab_default(self.p1, amount=12)
        self.assertEqual(self.collab_storage['residuals'], 12)
        self._collab_default(self.p1, amount=12)
        self.assertEqual(self.collab_storage['residuals'], 24)
        self._collab_default(self.p1, amount=12)
        self.assertEqual(self.collab_storage['residuals'], 36)

        # checking overflow:
        self._collab_default(self.p1, amount=12)
        self.assertEqual(self.collab_storage['residuals'], 48-42)

        # increasing threshold:
        self._collab_set_threshold(self.admin, 100)
        self._collab_default(self.p1, amount=50)
        self.assertEqual(self.collab_storage['residuals'], 6+8)

        self._collab_default(self.p1, amount=50)
        self.assertEqual(self.collab_storage['residuals'], 6+8+8)


    def test_wrong_share_configuration_lead_to_default_failwith(self):
        # making wrong collab just to test this case:
        originate_params = {
            self.p1:   {'share': 10, 'isCore': True},
            self.p2:   {'share': 10, 'isCore': True},
        }

        self._factory_create_proxy(self.admin, originate_params)
        self.collab_storage['totalShares'] = 18

        with self.assertRaises(MichelsonRuntimeError) as cm:
            self._collab_default(self.p2, amount=100)
        msg = 'Wrong share configuration'
        self.assertTrue(msg in str(cm.exception))


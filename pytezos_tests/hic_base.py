from pytezos import ContractInterface, pytezos, MichelsonRuntimeError
from unittest import TestCase
from os.path import dirname, join


COLLAB_FN = '../build/tz/hic_proxy.tz'
FACTORY_FN = '../build/tz/factory.tz'
SIGN_FN = '../build/tz/sign.tz'
PACKER_FN = '../build/tz/packer.tz'

HIC_PROXY_CODE = '../build/tz/lambdas/originate/hic_proxy.tz'


def split_amount(amount, shares, last_address):
    """ Splits amount according to the shares dict """

    total_shares = sum(shares.values())

    # calculating amounts, int always rounds down:
    amounts = {
        address: share * amount // total_shares
        for address, share in shares.items() if address != last_address
    }

    # dust goes to the last_address:
    accumulated_amount = sum(amounts.values())
    amounts[last_address] = amount - accumulated_amount

    # removing 0-operations:
    amounts = {
        address: amount for address, amount in amounts.items()
        if amount > 0
    }

    return amounts
  

class HicBaseCase(TestCase):

    def setUp(self):
        self.collab = ContractInterface.from_file(join(dirname(__file__), COLLAB_FN))
        self.factory = ContractInterface.from_file(join(dirname(__file__), FACTORY_FN))
        self.sign = ContractInterface.from_file(join(dirname(__file__), SIGN_FN))
        self.packer = ContractInterface.from_file(join(dirname(__file__), PACKER_FN))

        self.hic_proxy_code = open(join(dirname(__file__), HIC_PROXY_CODE)).read()

        # Two core participants:
        self.p1 = 'tz1iQE8ijR5xVPffBUPFubwB9XQJuyD9qsoJ'
        self.p2 = 'tz1MdaJfWzP5pPx3gwPxfdLZTHW6js9havos'

        # One just benefactor:
        self.tips = 'tz1RS9GoEXakf9iyBmSaheLMcakFRtzBXpWE'

        self.admin = self.p1

        self.mint_params = {
            'address': 'KT1VRdyXdMb452GRnSz7tPFQVg96bq2XAmSN',
            'amount': 1,
            'metadata': '697066733a2f2f516d5952724264554578587269473470526679746e666d596b664a4564417157793632683746327771346b517775',
            'royalties': 250
        }

        self.originate_params = {
            self.p1:   {'share': 330, 'isCore': True},
            self.p2:   {'share': 500, 'isCore': True},
            self.tips: {'share': 170, 'isCore': False}
        }

        self.swap_params = {
            'objkt_amount': 1,
            'objkt_id': 30000,
            'xtz_per_objkt': 10_000_000,
            'creator': self.p1,
            'royalties': 100
        }

        self.factory_storage = {
            'data': {
                'minterAddress': 'KT1Hkg5qeNhfwpKW4fXvq7HGZB9z2EnmCCA9',
                'marketplaceAddress': 'KT1HbQepzV1nVGg8QVznG7z4RcHseD5kwqBn',
                'registryAddress': 'KT1My1wDZHDGweCrJnQJi3wcFaS67iksirvj',
                'tokenAddress': 'KT1RJ6PbjHpwc3M5rw5s2Nbmefwbuwbdxton'
            },
            'templates': {
                'hic_contract': self.hic_proxy_code
            },
            'originatedContracts': {},
            'administrator': self.admin,
            'proposedAdministrator': None
        }

        self.result = None
        self.total_incomings = 0


    def _create_collab(self, sender, params, contract='hic_contract'):

        # converting params to bytes:
        params_bytes = self.packer.pack_originate_hic_proxy(
            params).interpret().storage.hex()

        create_params = {
            'templateName': contract,
            'params': params_bytes
        }

        result = self.factory.create_proxy(create_params).interpret(
            storage=self.factory_storage, sender=sender)
        self.factory_storage = result.storage

        self.assertEqual(len(result.operations), 1)

        operation = result.operations[0]
        self.assertTrue(operation['kind'] == 'origination')
        self.collab.storage_from_micheline(operation['script']['storage'])
        self.collab_storage = self.collab.storage()
        self.assertTrue(self.collab.storage()['administrator'] == sender)


    def _add_template(self, sender, template_name='added_template'):

        add_template_params = {
            'name': template_name,
            'originateFunc': self.hic_proxy_code
        }

        result = self.factory.add_template(add_template_params).interpret(
            storage=self.factory_storage, sender=sender)
        self.factory_storage = result.storage


    def _remove_template(self, sender, template_name='added_template'):

        result = self.factory.remove_template(template_name).interpret(
            storage=self.factory_storage, sender=sender)
        self.factory_storage = result.storage


    def _is_originated_contract(
        self, contract_address, sign_callback, sign_entrypoint):

        params = {
            'contractAddress': contract_address,
            'callback': sign_callback + '%' + sign_entrypoint
        }

        return self._call_view_entrypoint(
            self.factory.is_originated_contract, params, self.factory_storage)


    def _factory_update_admin(self, sender, proposed_admin):

        result = self.factory.update_admin(proposed_admin).interpret(
            storage=self.factory_storage, sender=sender)
        self.factory_storage = result.storage


    def _factory_accept_ownership(self, sender):

        result = self.factory.accept_ownership().interpret(
            storage=self.factory_storage, sender=sender)
        self.factory_storage = result.storage


    def _mint_call(self, sender):
        """ Testing that minting doesn't fail with default params """

        self.result = self.collab.mint_OBJKT(self.mint_params).interpret(
            storage=self.collab_storage, sender=sender)

        self.assertTrue(len(self.result.operations) == 1)
        operation = self.result.operations[0]

        self.assertEqual(operation['parameters']['entrypoint'], 'mint_OBJKT')
        op_bytes = operation['parameters']['value']['args'][1]['bytes']

        metadata = self.mint_params['metadata']
        self.assertEqual(op_bytes, metadata)

        self.assertEqual(operation['destination'],
            self.factory_storage['data']['minterAddress'])
        self.assertEqual(operation['amount'], '0')


    def _swap_call(self, sender):
        """ Testing that swapping doesn't fail with default params """

        self.result = self.collab.swap(self.swap_params).interpret(
            storage=self.collab_storage, sender=sender)

        assert len(self.result.operations) == 1
        assert self.result.operations[0]['parameters']['entrypoint'] == 'swap'
        # TODO: check that call goes to marketplaceAddress


    def _cancel_swap_call(self, sender):
        """ Testing that cancel swap doesn't fail with default params """

        some_swap_id = 42
        self.result = self.collab.cancel_swap(some_swap_id).interpret(
            storage=self.collab_storage, sender=sender)

        assert len(self.result.operations) == 1
        assert self.result.operations[0]['parameters']['entrypoint'] == 'cancel_swap'
        assert self.result.operations[0]['parameters']['value'] == {'int': '42'}
        # TODO: check that call goes to marketplaceAddress


    def _collect_call(self, sender):
        """ Testing that collect doesn't fail with default params """

        some_swap_id = 42
        self.result = self.collab.collect(some_swap_id).interpret(
            storage=self.collab_storage, sender=sender)

        assert len(self.result.operations) == 1
        assert self.result.operations[0]['parameters']['entrypoint'] == 'collect'
        assert self.result.operations[0]['parameters']['value']['int'] == '42'
        # TODO: check that call goes to marketplaceAddress


    def _curate_call(self, sender):
        """ Testing that curate doesn't fail with default params """

        curate_params = {'hDAO_amount': 100, 'objkt_id': 100_000}
        self.result = self.collab.curate(curate_params).interpret(
            storage=self.collab_storage, sender=sender)

        assert len(self.result.operations) == 1
        assert self.result.operations[0]['parameters']['entrypoint'] == 'curate'
        assert self.result.operations[0]['parameters']['value']['args'][0] == {'int': '100'}
        assert self.result.operations[0]['parameters']['value']['args'][1] == {'int': '100000'}
        # TODO: check that call goes to ?


    def _registry_call(self, sender):
        # TODO: implement this
        pass


    def _unregistry_call(self, sender):
        # TODO: implement this
        pass

        # TODO: test update manager
        # TODO: test pause
        # TODO: test views


    def _default_call(self, sender, amount):
        """ Testing that distribution in default call works properly """

        self.result = self.collab.default().with_amount(amount).interpret(
            storage=self.collab_storage, sender=sender)

        ops = self.result.operations
        # Operations is collected in reversed order
        # Order means because one (last) operation takes dust:
        ops = list(reversed(ops))

        shares = self.collab_storage['shares']
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


    def _call_view_entrypoint(self, entrypoint, params, storage):
        """ The returned operations from contract very similar for different
            entrypoints, so it require similar checks: """

        sign_callback, sign_entrypoint = params['callback'].split('%')

        self.result = entrypoint(params).interpret(
            storage=storage, sender=self.p1)

        assert len(self.result.operations) == 1
        op = self.result.operations[0]
        self.assertEqual(op['parameters']['entrypoint'], sign_entrypoint)
        self.assertEqual(op['destination'], sign_callback)

        return op['parameters']['value']['prim'] == 'True'


    def _is_core_participant_call(self, participant, sign_callback, sign_entrypoint):
        """ Testing that is_core_participant call emits correct callback """

        params = {
            'participantAddress': participant,
            'callback': sign_callback + '%' + sign_entrypoint
        }

        return self._call_view_entrypoint(
            self.collab.is_core_participant, params, self.collab_storage)


    def _is_minted_hash_call(self, metadata, sign_callback, sign_entrypoint):
        """ Testing that is_minted_hash call emits correct callback """

        params = {
            'metadata': metadata,
            'callback': sign_callback + '%' + sign_entrypoint
        }

        return self._call_view_entrypoint(
            self.collab.is_minted_hash, params, self.collab_storage)


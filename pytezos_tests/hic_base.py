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
  

# TODO: consider split this one big base case into separate:
# - one for collab
# - one for factory
# - one for signer
# ? It would be good to make them independent, but I want to support all
# this self.assert* methods, so I don't know how to make it good

# MAYBE: all this _factory / _sign should go to the BaseCase, so it would
# be possible to have different base cases for different collabs:
# - HicBaseCase for HicProxy & Bigmap one,
# - BasicBaseCase for BasicProxy
# etc

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

        self.random_contract_address = 'KT1Hkg5qeNhfwpKW4fXvq7HGZB9z2EnmCCA9'


    def _factory_create_proxy(self, sender, params, contract='hic_contract', amount=0):

        # converting params to bytes:
        params_bytes = self.packer.pack_originate_hic_proxy(
            params).interpret().storage.hex()

        create_params = {
            'templateName': contract,
            'params': params_bytes
        }

        result = self.factory.create_proxy(create_params).interpret(
            storage=self.factory_storage, sender=sender, amount=amount)
        self.factory_storage = result.storage

        self.assertEqual(len(result.operations), 1)

        operation = result.operations[0]
        self.assertTrue(operation['kind'] == 'origination')
        self.collab.storage_from_micheline(operation['script']['storage'])
        self.collab_storage = self.collab.storage()
        self.assertTrue(self.collab.storage()['administrator'] == sender)


    def _factory_add_template(self, sender, template_name='added_template', amount=0):

        add_template_params = {
            'name': template_name,
            'originateFunc': self.hic_proxy_code
        }

        result = self.factory.add_template(add_template_params).interpret(
            storage=self.factory_storage, sender=sender, amount=amount)
        self.factory_storage = result.storage


    def _factory_remove_template(self, sender, template_name='added_template', amount=0):

        result = self.factory.remove_template(template_name).interpret(
            storage=self.factory_storage, sender=sender, amount=amount)
        self.factory_storage = result.storage


    def _factory_is_originated_contract(
            self, contract_address=None, callback=None,
            entrypoint='random_entry', amount=0):

        contract_address = contract_address or self.random_contract_address
        callback = callback or self.random_contract_address

        params = {
            'contractAddress': contract_address,
            'callback': callback + '%' + entrypoint
        }

        return self._call_view_entrypoint(
            self.factory.is_originated_contract,
            params,
            self.factory_storage,
            amount=amount)


    def _factory_update_admin(self, sender, proposed_admin, amount=0):

        result = self.factory.update_admin(proposed_admin).interpret(
            storage=self.factory_storage, sender=sender, amount=amount)
        self.factory_storage = result.storage
        # TODO: implement some checks?


    def _factory_accept_ownership(self, sender, amount=0):

        result = self.factory.accept_ownership().interpret(
            storage=self.factory_storage, sender=sender, amount=amount)
        self.factory_storage = result.storage
        # TODO: implement some checks?


    def _collab_mint(self, sender, amount=0):
        """ Testing that minting doesn't fail with default params """

        self.result = self.collab.mint_OBJKT(self.mint_params).interpret(
            storage=self.collab_storage, sender=sender, amount=amount)

        self.assertTrue(len(self.result.operations) == 1)
        operation = self.result.operations[0]

        self.assertEqual(operation['parameters']['entrypoint'], 'mint_OBJKT')
        op_bytes = operation['parameters']['value']['args'][1]['bytes']

        metadata = self.mint_params['metadata']
        self.assertEqual(op_bytes, metadata)

        self.assertEqual(operation['destination'],
            self.factory_storage['data']['minterAddress'])
        self.assertEqual(operation['amount'], '0')


    def _collab_swap(self, sender, amount=0):
        """ Testing that swapping doesn't fail with default params """

        self.result = self.collab.swap(self.swap_params).interpret(
            storage=self.collab_storage, sender=sender, amount=amount)

        assert len(self.result.operations) == 1
        assert self.result.operations[0]['parameters']['entrypoint'] == 'swap'
        # TODO: check that call goes to marketplaceAddress


    def _collab_cancel_swap(self, sender, amount=0):
        """ Testing that cancel swap doesn't fail with default params """

        some_swap_id = 42
        self.result = self.collab.cancel_swap(some_swap_id).interpret(
            storage=self.collab_storage, sender=sender, amount=amount)

        assert len(self.result.operations) == 1
        assert self.result.operations[0]['parameters']['entrypoint'] == 'cancel_swap'
        assert self.result.operations[0]['parameters']['value'] == {'int': '42'}
        # TODO: check that call goes to marketplaceAddress


    def _collab_collect(self, sender, amount=0):
        """ Testing that collect doesn't fail with default params """

        some_swap_id = 42
        self.result = self.collab.collect(some_swap_id).interpret(
            storage=self.collab_storage, sender=sender, amount=amount)

        assert len(self.result.operations) == 1
        assert self.result.operations[0]['parameters']['entrypoint'] == 'collect'
        assert self.result.operations[0]['parameters']['value']['int'] == '42'
        # TODO: check that call goes to marketplaceAddress


    def _collab_curate(self, sender, amount=0):
        """ Testing that curate doesn't fail with default params """

        curate_params = {'hDAO_amount': 100, 'objkt_id': 100_000}
        self.result = self.collab.curate(curate_params).interpret(
            storage=self.collab_storage, sender=sender, amount=amount)

        assert len(self.result.operations) == 1
        assert self.result.operations[0]['parameters']['entrypoint'] == 'curate'
        assert self.result.operations[0]['parameters']['value']['args'][0] == {'int': '100'}
        assert self.result.operations[0]['parameters']['value']['args'][1] == {'int': '100000'}
        # TODO: check that call goes to ?


    def _collab_registry(self, sender, amount=0):
        # TODO: implement this
        pass


    def _collab_unregistry(self, sender, amount=0):
        # TODO: implement this
        pass

        # TODO: test update manager
        # TODO: test pause
        # TODO: test views


    def _collab_default(self, sender, amount):
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


    def _call_view_entrypoint(self, entrypoint, params, storage, amount=0):
        """ The returned operations from contract very similar for different
            entrypoints, so it require similar checks: """

        # Works for factory & collabs both, this is why storage parameter
        # transfered. TODO: Maybe it would be better to use attrib name?
        callback, entrypoint_name = params['callback'].split('%')

        self.result = entrypoint(params).interpret(
            storage=storage, sender=self.p1, amount=amount)

        assert len(self.result.operations) == 1
        op = self.result.operations[0]
        self.assertEqual(op['parameters']['entrypoint'], entrypoint_name)
        self.assertEqual(op['destination'], callback)

        return op['parameters']['value']['prim'] == 'True'


    def _collab_is_core_participant_call(
            self, participant, callback=None,
            entrypoint='random_entry', amount=0):
        """ Testing that is_core_participant call emits correct callback """

        callback = callback or self.random_contract_address

        params = {
            'participantAddress': participant,
            'callback': callback + '%' + entrypoint
        }

        return self._call_view_entrypoint(
            self.collab.is_core_participant,
            params,
            self.collab_storage,
            amount=amount)


    def _collab_update_operators(self, sender, amount=0):
        # TODO: not implemented
        pass


    def _collab_is_administrator_call(
            self, participant, callback=None,
            entrypoint='random_entry', amount=0):
        """ Testing that is_administrator call emits correct callback """

        callback = callback or self.random_contract_address

        # TODO: not implemented
        pass


    def _collab_get_total_shares(
            self, callback=None,
            entrypoint='random_entry', amount=0):
        """ Testing that get_total_shares call emits correct callback """

        callback = callback or self.random_contract_address

        # TODO: not implemented
        pass


    def _collab_get_participant_shares(
            self, participant, callback=None,
            entrypoint='random_entry', amount=0):
        """ Testing that get_participant_shares call emits correct callback """

        callback = callback or self.random_contract_address

        # TODO: not implemented
        pass


    def _collab_update_admin(self, sender, proposed_admin, amount=0):

        result = self.collab.update_admin(proposed_admin).interpret(
            storage=self.collab_storage, sender=sender, amount=amount)
        self.collab_storage = result.storage
        # TODO: implement some checks?


    def _collab_accept_ownership(self, sender, amount=0):

        result = self.collab.accept_ownership().interpret(
            storage=self.collab_storage, sender=sender, amount=amount)
        self.collab_storage = result.storage
        # TODO: implement some checks?


    def _collab_trigger_pause(self, sender, amount=0):

        # TODO: not implemented
        pass


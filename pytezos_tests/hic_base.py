from pytezos import ContractInterface, pytezos, MichelsonRuntimeError
from unittest import TestCase
from os.path import dirname, join
import codecs
from test_data import (
    COLLAB_FN, FACTORY_FN, SIGN_FN, PACKER_FN, HIC_PROXY_CODE,
    LAMBDA_CALLS, load_lambdas, DEFAULT_PARAMS
)


def str_to_hex_bytes(string):
    return codecs.encode(string.encode("ascii"), "hex")


def filter_zero(dct):
    return {key: value for key, value in dct.items() if value > 0}


def sum_dicts(dct_a, dct_b):
    keys = set([*dct_a, *dct_b])
    return {key: dct_a.get(key, 0) + dct_b.get(key, 0) for key in keys}


def split_amount(amount, shares):
    """ Splits amount according to the shares dict """

    total_shares = sum(shares.values())

    # calculating amounts, int always rounds down:
    amounts = {
        address: share * amount // total_shares
        for address, share in shares.items()
    }

    accumulated_amount = sum(amounts.values())
    residuals = amount - accumulated_amount

    return amounts, residuals


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

        self.default_params = DEFAULT_PARAMS

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

        self.addresses = {
            'hicMinterAddress': 'KT1Hkg5qeNhfwpKW4fXvq7HGZB9z2EnmCCA9',
            'hicMarketplaceAddress': 'KT1HbQepzV1nVGg8QVznG7z4RcHseD5kwqBn',
            'hicRegistryAddress': 'KT1My1wDZHDGweCrJnQJi3wcFaS67iksirvj',
            'hicTokenAddress': 'KT1RJ6PbjHpwc3M5rw5s2Nbmefwbuwbdxton'
        }

        self.factory_storage = {
            'records': {
                name: self._pack_address(address)
                for name, address in self.addresses.items()
            },
            'templates': {
                'hic_contract': self.hic_proxy_code
            },
            'originatedContracts': {},
            'administrator': self.admin,
            'proposedAdministrator': None
        }

        self.sign_storage = {}

        self.result = None
        self.total_incomings = 0

        self.random_contract_address = 'KT1Hkg5qeNhfwpKW4fXvq7HGZB9z2EnmCCA9'
        self.lambdas = load_lambdas(LAMBDA_CALLS)

        # default execute_lambda call params:
        self.execute_params = self._prepare_lambda_params('mint_OBJKT')


    def _pack_address(self, address):
        return self.packer.pack_address(address).interpret().storage.hex()


    def _pack_nat(self, nat):
        return self.packer.pack_nat(nat).interpret().storage.hex()


    def _prepare_lambda_params(self, entrypoint_name):
        """ Returns dict with some default lambda params for given entrypoint
        """

        packer_call = getattr(self.packer, f'pack_{entrypoint_name}')
        packed_bytes = packer_call(
            self.default_params[entrypoint_name]).interpret().storage.hex()

        execute_params = {
            'lambda': self.lambdas[f'hic_{entrypoint_name}'],
            'packedParams': packed_bytes
        }

        return execute_params


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

        result = self._call_view_entrypoint(
            self.factory.is_originated_contract,
            params,
            self.factory_storage,
            callback,
            entrypoint,
            amount=amount)

        return result.operations[0]['parameters']['value']['prim'] == 'True'


    def _factory_update_admin(self, sender, proposed_admin, amount=0):

        result = self.factory.update_admin(proposed_admin).interpret(
            storage=self.factory_storage, sender=sender, amount=amount)
        self.factory_storage = result.storage

        self.assertEqual(
            self.factory_storage['proposedAdministrator'],
            proposed_admin)


    def _factory_accept_ownership(self, sender, amount=0):

        result = self.factory.accept_ownership().interpret(
            storage=self.factory_storage, sender=sender, amount=amount)
        self.factory_storage = result.storage

        self.assertEqual(
            self.factory_storage['administrator'],
            sender)


    def _factory_add_record(
            self, sender, name='without name', value=None, amount=0):

        value = self._pack_nat(42) if value is None else value
        params = dict(name=name, value=value)

        result = self.factory.add_record(params).interpret(
            storage=self.factory_storage, sender=sender, amount=amount)
        self.factory_storage = result.storage

        recorded_value = self.factory_storage['records'][name]
        self.assertEqual(recorded_value, bytes.fromhex(value))


    def _factory_remove_record(self, sender, name='without name', amount=0):

        result = self.factory.remove_record(name).interpret(
            storage=self.factory_storage, sender=sender, amount=amount)

        self.assertEqual(result.storage['records'][name], None)
        result.storage['records'].pop(name)

        self.factory_storage = result.storage


    def _collab_mint(self, sender, amount=0):
        """ Testing that minting doesn't fail with default params """

        self.result = self.collab.mint_OBJKT(
            self.default_params['mint_OBJKT']).interpret(
            storage=self.collab_storage, sender=sender, amount=amount)

        self.assertTrue(len(self.result.operations) == 1)
        operation = self.result.operations[0]

        self.assertEqual(operation['parameters']['entrypoint'], 'mint_OBJKT')
        op_bytes = operation['parameters']['value']['args'][1]['bytes']

        metadata = self.default_params['mint_OBJKT']['metadata']
        self.assertEqual(op_bytes, metadata)

        self.assertEqual(operation['destination'],
            self.addresses['hicMinterAddress'])
        self.assertEqual(operation['amount'], '0')


    def _collab_swap(self, sender, amount=0):
        """ Testing that swapping doesn't fail with default params """

        self.result = self.collab.swap(self.swap_params).interpret(
            storage=self.collab_storage, sender=sender, amount=amount)

        assert len(self.result.operations) == 1
        assert self.result.operations[0]['parameters']['entrypoint'] == 'swap'
        self.assertEqual(
            self.result.operations[0]['destination'],
            self.collab_storage['marketplaceAddress']
        )


    def _collab_cancel_swap(self, sender, amount=0):
        """ Testing that cancel swap doesn't fail with default params """

        some_swap_id = 42
        self.result = self.collab.cancel_swap(some_swap_id).interpret(
            storage=self.collab_storage, sender=sender, amount=amount)

        assert len(self.result.operations) == 1
        assert self.result.operations[0]['parameters']['entrypoint'] == 'cancel_swap'
        assert self.result.operations[0]['parameters']['value'] == {'int': '42'}
        self.assertEqual(
            self.result.operations[0]['destination'],
            self.collab_storage['marketplaceAddress']
        )


    def _collab_collect(self, sender, amount=0):
        """ Testing that collect doesn't fail with default params """

        some_swap_id = 42
        self.result = self.collab.collect(some_swap_id).interpret(
            storage=self.collab_storage, sender=sender, amount=amount)

        assert len(self.result.operations) == 1
        assert self.result.operations[0]['parameters']['entrypoint'] == 'collect'
        assert self.result.operations[0]['parameters']['value']['int'] == '42'
        self.assertEqual(
            self.result.operations[0]['destination'],
            self.collab_storage['marketplaceAddress']
        )


    def _collab_registry(self, sender, amount=0):

        metadata = str_to_hex_bytes(
            'ipfs://QmVJzbVtq1sc8Cj2ZJFJmSBZVWfLDvsL3asuimUBvMARiB')
        subjkt = str_to_hex_bytes('MEGA COLLABA')

        registry_params = {
            'metadata': metadata,
            'subjkt': subjkt
        }

        self.result = self.collab.registry(registry_params).interpret(
            storage=self.collab_storage, sender=sender, amount=amount)

        assert len(self.result.operations) == 1
        assert self.result.operations[0]['parameters']['entrypoint'] == 'registry'
        self.assertEqual(
            self.result.operations[0]['destination'],
            self.collab_storage['registryAddress']
        )


    def _collab_unregistry(self, sender, amount=0):

        self.result = self.collab.unregistry().interpret(
            storage=self.collab_storage, sender=sender, amount=amount)

        assert len(self.result.operations) == 1
        assert self.result.operations[0]['parameters']['entrypoint'] == 'unregistry'
        self.assertEqual(
            self.result.operations[0]['destination'],
            self.collab_storage['registryAddress']
        )


    def _collab_default(self, sender, amount):
        """ Testing that distribution in default call works properly """

        self.result = self.collab.default().with_amount(amount).interpret(
            storage=self.collab_storage, sender=sender)

        ops = self.result.operations
        # Operations is collected in reversed order
        # Order means because one (last) operation takes dust:
        ops = list(reversed(ops))

        shares = self.collab_storage['shares']
        dist_amount = amount + self.collab_storage['residuals']
        calc_amounts, residuals = split_amount(dist_amount, shares)
        self.assertEqual(residuals, self.result.storage['residuals'])

        undistributed = self.collab_storage['undistributed']
        threshold = self.collab_storage['threshold']
        calc_amounts = sum_dicts(calc_amounts, undistributed)

        new_undistributed = {
            address: 0 if amount >= threshold else amount
            for address, amount in calc_amounts.items()
        }

        calc_amounts = filter_zero({
            address: 0 if amount < threshold else amount
            for address, amount in calc_amounts.items()
        })

        # Checking that sum of the operations is correct and no dust is left
        ops_sum = sum(int(op['amount']) for op in ops)
        exp_sum = sum(calc_amounts.values())
        self.assertEqual(ops_sum, exp_sum)
        self.assertEqual(len(ops), len(calc_amounts))

        # Checking that each participant get amount he should receive:
        amounts = {op['destination']: int(op['amount']) for op in ops}

        self.assertEqual(calc_amounts, amounts)
        self.assertEqual(new_undistributed, self.result.storage['undistributed'])

        self.collab_storage = self.result.storage


    def _call_view_entrypoint(
            self, entrypoint, params, storage, callback,
            entrypoint_name, amount=0):
        """ The returned operations from contract very similar for different
            entrypoints, so it require similar checks: """

        # Works for factory & collabs both, this is why storage parameter
        # transfered. TODO: Maybe it would be better to use attrib name?

        self.result = entrypoint(params).interpret(
            storage=storage, sender=self.p1, amount=amount)

        assert len(self.result.operations) == 1
        op = self.result.operations[0]
        self.assertEqual(op['parameters']['entrypoint'], entrypoint_name)
        self.assertEqual(op['destination'], callback)

        return self.result


    def _collab_update_operators(
            self, sender, operator=None, token_id=0, amount=0):

        operator = operator or self.collab_storage['marketplaceAddress']

        # self.collab.address is empty, so using random contract address instead:
        owner = self.random_contract_address

        update_operatiors_params = [{
            'add_operator': {
                'owner': owner,
                'operator': operator,
                'token_id': token_id}
        }]

        result = (self.collab
            .update_operators(update_operatiors_params)
            .with_amount(amount)
            .interpret(storage=self.collab_storage, sender=sender))

        self.collab_storage = result.storage

        self.assertEqual(len(result.operations), 1)
        op = result.operations[0]
        self.assertEqual(
            op['destination'],
            self.collab_storage['tokenAddress'])

        self.assertEqual(op['parameters']['entrypoint'], 'update_operators')


    def _collab_update_admin(self, sender, proposed_admin, amount=0):

        result = self.collab.update_admin(proposed_admin).interpret(
            storage=self.collab_storage, sender=sender, amount=amount)
        self.collab_storage = result.storage

        self.assertEqual(
            self.collab_storage['proposedAdministrator'],
            proposed_admin)


    def _collab_accept_ownership(self, sender, amount=0):

        result = self.collab.accept_ownership().interpret(
            storage=self.collab_storage, sender=sender, amount=amount)
        self.collab_storage = result.storage

        self.assertEqual(
            self.collab_storage['administrator'],
            sender)


    def _collab_execute(self, sender, params=None, amount=0):

        params = params or self.execute_params

        result = self.collab.execute(params).interpret(
            storage=self.collab_storage, sender=sender, amount=amount)
        self.collab_storage = result.storage

        return result


    def _sign_sign(self, sender, objkt_id=0, amount=0):

        result = self.sign.sign(objkt_id).interpret(
            storage=self.sign_storage, sender=sender, amount=amount)

        self.assertTrue((sender, objkt_id) in result.storage)
        self.sign_storage = result.storage


    def _sign_unsign(self, sender, objkt_id=0, amount=0):

        result = self.sign.unsign(objkt_id).interpret(
            storage=self.sign_storage, sender=sender, amount=amount)

        key = (sender, objkt_id)
        self.assertTrue(result.storage[key] is None)
        result.storage.pop(key)
        self.sign_storage = result.storage


    def _sign_is_signed(
            self, participant=None, objkt_id=0, callback=None,
            entrypoint='random_entry', amount=0):

        callback = callback or self.random_contract_address
        participant = participant or self.p1

        params = {
            'participant': participant,
            'id': objkt_id,
            'callback': callback + '%' + entrypoint
        }

        result = self._call_view_entrypoint(
            self.sign.is_signed,
            params,
            self.sign_storage,
            callback,
            entrypoint,
            amount=amount)

        return result.operations[0]['parameters']['value']['prim'] == 'True'


    def _collab_get_administrator(self):
        call = self.collab.get_administrator()
        return call.onchain_view(storage=self.collab_storage)


    def _collab_get_shares(self):
        call = self.collab.get_shares()
        return call.onchain_view(storage=self.collab_storage)


    def _collab_get_total_shares(self):
        call = self.collab.get_total_shares()
        return call.onchain_view(storage=self.collab_storage)


    def _collab_get_core_participants(self):
        call = self.collab.get_core_participants()
        return call.onchain_view(storage=self.collab_storage)


    def _collab_get_total_received(self):
        call = self.collab.get_total_received()
        return call.onchain_view(storage=self.collab_storage)


    def _collab_set_threshold(self, sender=None, threshold=0, amount=0):
        sender = sender or self.admin
        result = self.collab.set_threshold(threshold).interpret(
            storage=self.collab_storage,
            sender=sender,
            amount=amount
        )

        self.assertEqual(result.storage['threshold'], threshold)
        self.collab_storage = result.storage


    def _collab_withdraw(self, sender=None, recipient=None, amount=0):
        sender = sender or self.admin
        recipient = recipient or self.admin

        result = self.collab.withdraw(recipient).interpret(
            storage=self.collab_storage,
            sender=sender,
            amount=amount
        )

        self.assertEqual(result.storage['undistributed'][recipient], 0)
        self.assertEqual(len(result.operations), 1)
        op = result.operations[0]
        origin_undistributed = self.collab_storage['undistributed'][recipient]
        withdrawn_amount = int(op['amount'])
        self.assertEqual(withdrawn_amount, origin_undistributed)
        self.assertEqual(op['destination'], recipient)

        self.collab_storage = result.storage

        return withdrawn_amount


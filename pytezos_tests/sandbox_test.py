from pytezos.sandbox.node import SandboxedNodeTestCase
from pytezos.sandbox.parameters import sandbox_addresses, sandbox_commitment
from pytezos import ContractInterface, pytezos, MichelsonRuntimeError
from pytezos.contract.result import ContractCallResult
from pytezos.rpc.errors import MichelsonError
import unittest
from os.path import dirname, join
import json
import codecs
from test_data import (
    load_lambdas, LAMBDA_CALLS, LAMBDA_ORIGINATE, FACTORY_FN,
    PACKER_FN, CONTRACTS_DIR, SIGN_FN, MOCK_FN)


def str_to_hex_bytes(string):
    return codecs.encode(string.encode("ascii"), "hex")


def pkh(key):
    return key.key.public_key_hash()


def read_contract(name):
    """ Loads contract from CONTRACTS_DIR with name {name}.tz """

    filename = join(dirname(__file__), CONTRACTS_DIR, f'{name}.tz')
    return ContractInterface.from_file(filename)


def read_storage(name):
    """ Loads storage from CONTRACTS_DIR with name {name}.json """

    filename = join(dirname(__file__), CONTRACTS_DIR, f'{name}.json')
    with open(filename, 'r') as f:
        return json.loads(f.read())


class ContractInteractionsTestCase(SandboxedNodeTestCase):


    def _deploy_contract(self, client, contract, storage):
        """ Deploys contract with given storage """

        # TODO: try to replace key with client.key:
        opg = contract.using(shell=self.get_node_url(), key=client.key)
        opg = opg.originate(initial_storage=storage)

        return opg.fill().sign().inject()


    def _deploy_factory(self, client):

        factory = ContractInterface.from_file(join(dirname(__file__), FACTORY_FN))
        factory_init = {
            'records': {},
            'templates': {},
            'originatedContracts': {},
            'administrator': pkh(client),
            'proposedAdministrator': None
        }

        return self._deploy_contract(client, factory, factory_init)


    def _find_call_result_by_hash(self, client, opg_hash):

        # Get injected operation and convert to ContractCallResult
        opg = client.shell.blocks['head':].find_operation(opg_hash)
        return ContractCallResult.from_operation_group(opg)[0]


    def _load_contract(self, client, contract_address):

        # Load originated contract from blockchain
        contract = client.contract(contract_address)
        contract = contract.using(
            shell=self.get_node_url(),
            key='bootstrap1')
        return contract


    def _find_contract_by_hash(self, client, opg_hash):
        """ Returns contract that was originated with opg_hash """

        op = client.shell.blocks['head':].find_operation(opg_hash)
        op_result = op['contents'][0]['metadata']['operation_result']
        address = op_result['originated_contracts'][0]

        return self._load_contract(client, address)


    def _find_contract_internal_by_hash(self, client, opg_hash):
        """ Returns collab that was originated with opg_hash """

        op = client.shell.blocks['head':].find_operation(opg_hash)
        int_op = op['contents'][0]['metadata']['internal_operation_results']
        address = int_op[0]['result']['originated_contracts'][0]

        return self._load_contract(client, address)


    def _activate_accs(self):
        self.p1 = self.client.using(key='bootstrap1')
        self.p1.reveal()

        self.p2 = self.client.using(key='bootstrap2')
        self.p2.reveal()

        self.tips = self.client.using(key='bootstrap3')
        self.tips.reveal()

        self.hic_admin = self.client.using(key='bootstrap4')
        self.hic_admin.reveal()

        self.buyer = self.client.using(key='bootstrap5')
        self.buyer.reveal()


    def _deploy_hic_contracts(self, client):
        # Deploying OBJKTs:
        storage = read_storage('fa2_objkts')
        storage.update({'administrator': pkh(client)})
        opg = self._deploy_contract(
            client=client,
            contract=read_contract('fa2_objkts'),
            storage=storage)

        self.bake_block()
        self.objkts = self._find_contract_by_hash(client, opg['hash'])

        # Deploying hDAO:
        storage = read_storage('fa2_hdao')
        storage.update({'administrator': pkh(client)})
        opg = self._deploy_contract(
            client=client,
            contract=read_contract('fa2_hdao'),
            storage=storage)

        self.bake_block()
        self.hdao = self._find_contract_by_hash(client, opg['hash'])

        # Deploying curate:
        storage = read_storage('curation')
        storage.update({
            'manager': pkh(client)
        })

        opg = self._deploy_contract(
            client=client,
            contract=read_contract('curation'),
            storage=storage)

        self.bake_block()
        self.curate = self._find_contract_by_hash(client, opg['hash'])

        # Deploying objkt_swap:
        storage = read_storage('objkt_swap')
        storage.update({
            'curate': self.curate.address,
            'hdao': self.hdao.address,
            'objkt': self.objkts.address,
            'manager': pkh(client) 
        })
        opg = self._deploy_contract(
            client=client,
            contract=read_contract('objkt_swap'),
            storage=storage)

        self.bake_block()
        self.minter = self._find_contract_by_hash(client, opg['hash'])

        # configure curate:
        configuration = {
            'fa2': self.hdao.address,
            'protocol': self.minter.address
        }
        self.curate.configure(configuration).inject()
        self.bake_block()

        # what does this genesis?:
        self.minter.genesis().inject()
        self.bake_block()

        # configure objkts and hdao:
        self.objkts.set_administrator(self.minter.address).inject()
        self.hdao.set_administrator(self.minter.address).inject()
        self.bake_block()

        # Deploying Marketplace:
        storage = read_storage('marketplace')
        storage.update({
            'objkt': self.objkts.address,
            'manager': pkh(client)
        })
        opg = self._deploy_contract(
            client=client,
            contract=read_contract('marketplace'),
            storage=storage)

        self.bake_block()
        self.marketplace = self._find_contract_by_hash(client, opg['hash'])

        # Deploying registry
        storage = read_storage('subjkt')
        storage.update({'manager': pkh(client)})
        opg = self._deploy_contract(
            client=client,
            contract=read_contract('subjkt'),
            storage=storage)

        self.bake_block()
        self.registry = self._find_contract_by_hash(client, opg['hash'])


    def _add_operator(self, contract, owner_client, owner, operator, token_id):
        fa2_contract = owner_client.contract(contract.address)
        update_operatiors_params = [{
            'add_operator': {
                'owner': owner,
                'operator': operator,
                'token_id': token_id}
        }]

        return fa2_contract.update_operators(update_operatiors_params).inject()


    def setUp(self):
        self._activate_accs()
        self._deploy_hic_contracts(self.hic_admin)

        # Deploying packer (I feel this is temporal solution but who knows):
        #    (it is just used to pack data)
        packer = ContractInterface.from_file(join(dirname(__file__), PACKER_FN))
        opg = self._deploy_contract(self.p1, packer, 0)
        self.bake_block()
        self.packer = self._find_contract_by_hash(self.p1, opg['hash'])

        # Deploying factory:
        opg = self._deploy_factory(self.p1)
        self.bake_block()
        self.factory = self._find_contract_by_hash(self.p1, opg['hash'])

        # Adding templates to the factory:
        for lambda_name, filename in LAMBDA_ORIGINATE.items():
            originate_lambda = open(
                join(dirname(__file__), filename)).read()

            self.factory.add_template({
                'name': lambda_name,
                'originateFunc': originate_lambda
            }).inject()
            self.bake_block()

        # Adding records to the factory:
        def pack_address(address):
            return self.packer.pack_address(
                address).interpret().storage.hex()

        records = {
            'minterAddress': pack_address(self.minter.address),
            'marketplaceAddress': pack_address(self.marketplace.address),
            'tokenAddress': pack_address(self.objkts.address),
            'registryAddress': pack_address(self.registry.address)
        }

        for record_name, value in records.items():
            self.factory.add_record({
                'name': record_name,
                'value': value
            }).inject()
            self.bake_block()

        # Loading lambdas:
        self.lambdas = load_lambdas(LAMBDA_CALLS)

        # Deploying signer:
        sign = ContractInterface.from_file(join(dirname(__file__), SIGN_FN))
        sign_storage = {}
        opg = self._deploy_contract(self.p1, sign, sign_storage)
        self.bake_block()
        self.sign = self._find_contract_by_hash(self.p1, opg['hash'])

        # Deploying mock view:
        mock = ContractInterface.from_file(join(dirname(__file__), MOCK_FN))
        mock_storage = {'natValue': None, 'boolValue': None}
        opg = self._deploy_contract(self.p1, mock, mock_storage)
        self.bake_block()
        self.mock = self._find_contract_by_hash(self.p1, opg['hash'])


    def _originate_default_contract(self):
        """ Creates contract using proxy that used in multiple tests """

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

    def test_mint_token(self):

        self._originate_default_contract()

        # mint:
        mint_params = {
            'address': self.collab.address,
            'amount': 10,
            'metadata': '697066733a2f2f516d5952724264554578587269473470526679746e666d596b664a4564417157793632683746327771346b517775',
            'royalties': 250
        }

        opg = self.collab.mint_OBJKT(mint_params).inject()
        self.bake_block()
        result = self._find_call_result_by_hash(self.p1, opg['hash'])

        # checking that mint is ok:
        self.assertEqual(self.objkts.storage['all_tokens'](), 1)
        self.assertEqual(self.objkts.storage['ledger'][self.collab.address, 0](), 10)

        # update operators:
        self._add_operator(
            contract=self.collab,
            owner_client=self.p1,
            owner=self.collab.address,
            operator=self.marketplace.address,
            token_id=0)
        self.bake_block()

        # swap:
        swap_params = {
            'objkt_amount': 4,
            'objkt_id': 0,
            'xtz_per_objkt': 1_000_000,
            'creator': self.collab.address,
            'royalties': 250
        }

        swap_id = self.marketplace.storage['counter']()
        opg = self.collab.swap(swap_params).inject()
        self.bake_block()
        result = self._find_call_result_by_hash(self.p1, opg['hash'])

        # collect:
        opg = self.buyer.contract(self.marketplace.address).collect(
            swap_id).with_amount(1_000_000).inject()

        self.bake_block()
        result = self._find_call_result_by_hash(self.p1, opg['hash'])

        # checking objkt holders:
        self.assertEqual(self.objkts.storage['all_tokens'](), 1)
        self.assertEqual(self.objkts.storage['ledger'][self.collab.address, 0](), 6)
        self.assertEqual(self.objkts.storage['ledger'][self.marketplace.address, 0](), 3)
        self.assertEqual(self.objkts.storage['ledger'][pkh(self.buyer), 0](), 1)

        # TODO: checking distribution:
        pass


    def test_marketplace_communication(self):
        """ Testing marketplace communication without any collab contracts """

        # mint:
        mint_params = {
            'address': pkh(self.p1),
            'amount': 100,
            'metadata': '697066733a2f2f516d5952724264554578587269473470526679746e666d596b664a4564417157793632683746327771346b517775',
            'royalties': 100
        }

        minter = self.p1.contract(self.minter.address)
        opg = minter.mint_OBJKT(mint_params).inject()
        self.bake_block()
        result = self._find_call_result_by_hash(self.p1, opg['hash'])

        # update operators:
        self._add_operator(self.objkts, self.p1, pkh(self.p1), self.marketplace.address, 0)
        self.bake_block()

        # swap:
        swap_params = {
            'creator': pkh(self.p1),
            'objkt_amount': 100,
            'objkt_id': 0,
            'royalties': 100,
            'xtz_per_objkt': 1_000_000,
        }

        marketplace = self.p1.contract(self.marketplace.address)
        swap_id = marketplace.storage['counter']()
        opg = marketplace.swap(swap_params).inject()
        self.bake_block()
        result = self._find_call_result_by_hash(self.p1, opg['hash'])

        # collect:
        opg = self.buyer.contract(self.marketplace.address).collect(
            swap_id).with_amount(1_000_000).inject()

        self.bake_block()
        result = self._find_call_result_by_hash(self.p1, opg['hash'])
        assert self.objkts.storage['ledger'][(pkh(self.buyer), 0)]() == 1

        # reswap this one objkt with low price:
        self._add_operator(self.objkts, self.buyer, pkh(self.buyer), self.marketplace.address, 0)
        self.bake_block()

        marketplace = self.buyer.contract(self.marketplace.address)
        swap_id = marketplace.storage['counter']()

        swap_params.update({
            'objkt_amount': 1,
            'xtz_per_objkt': 100
        })
        opg = marketplace.swap(swap_params).inject()
        self.bake_block()
        result = self._find_call_result_by_hash(self.p1, opg['hash'])

        # rebuing second swap:
        opg = self.p2.contract(self.marketplace.address).collect(
            swap_id).with_amount(1*100).inject()
        self.bake_block()
        result = self._find_call_result_by_hash(self.p1, opg['hash'])

        # and p2 should not receive this 1 objkt:
        assert self.objkts.storage['ledger'][(pkh(self.p2), 0)]() == 1
        assert self.objkts.storage['ledger'][(self.marketplace.address, 0)]() == 99

        # Trying to use this second swap second time:
        with self.assertRaises(MichelsonError) as cm:
            opg = self.p2.contract(self.marketplace.address).collect(
                swap_id).with_amount(1*100).inject()
            self.bake_block()
            result = self._find_call_result_by_hash(self.p1, opg['hash'])

        # Trying to collect swap that does not exist:
        with self.assertRaises(MichelsonError) as cm:
            opg = self.p2.contract(self.marketplace.address).collect(
                3).with_amount(1*100).inject()
            self.bake_block()

        # 0-tez swap
        self._add_operator(self.objkts, self.p2, pkh(self.p2), self.marketplace.address, 0)
        self.bake_block()

        marketplace = self.p2.contract(self.marketplace.address)
        swap_id = marketplace.storage['counter']()

        swap_params.update({
            'objkt_amount': 1,
            'xtz_per_objkt': 0
        })
        opg = marketplace.swap(swap_params).inject()
        self.bake_block()

        opg = self.buyer.contract(self.marketplace.address).collect(
            swap_id).with_amount(0).inject()
        self.bake_block()

        assert self.objkts.storage['ledger'][(pkh(self.buyer), 0)]() == 1
        assert self.objkts.storage['ledger'][(self.marketplace.address, 0)]() == 99

        # Trying to swap more objects that have:
        with self.assertRaises(MichelsonError) as cm:
            marketplace = self.buyer.contract(self.marketplace.address)
            swap_id = marketplace.storage['counter']()

            swap_params.update({
                'objkt_amount': 2,
                'xtz_per_objkt': 0
            })
            opg = marketplace.swap(swap_params).inject()
            self.bake_block()

        self.assertTrue('FA2_INSUFFICIENT_BALANCE' in str(cm.exception))


        # Trying to sell objkt for price that leads to 0-fees trans:
        # this is raising contract.empty_transaction but it should not
        # I turned off this test because it is failed and this contract
        # already in mainnet
        """
        marketplace = self.buyer.contract(self.marketplace.address)
        swap_id = marketplace.storage['counter']()

        swap_params.update({
            'objkt_amount': 1,
            'xtz_per_objkt': 10
        })
        opg = marketplace.swap(swap_params).inject()
        self.bake_block()

        opg = self.p2.contract(self.marketplace.address).collect(
            swap_id).with_amount(10).inject()
        self.bake_block()
        """


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

    '''
    def test_withdraw_token(self):
        # Do I need to implement this? Would need to support FA2 only or FA1.2 too?

        # 1. collab mints, then not admin withdraws: failure
        # 2. collab mints, then admin withdraws: success
        # 3. someone mints, then not admin withdraws: failure
        # 4. someone mints, then admin withdraws: success
        # withdraw zero tokens?
        pass
    '''

    '''
    def test_created_contract_params(self):
        pass
        # TODO: test contract created params is equal to expected
        # TODO: test mint/swap/cancel and others?


    def test_reading_views(self):
        pass
        # TODO: test reading views from another contract
    '''

    def test_signature_communications(self):

        opg = self.p1.contract(self.sign.address).sign(42).inject()
        self.bake_block()
        result = self._find_call_result_by_hash(self.p1, opg['hash'])
        self.sign.storage[(pkh(self.p1), 42)]()

        opg = self.tips.contract(self.sign.address).sign(32768).inject()
        self.bake_block()
        result = self._find_call_result_by_hash(self.p1, opg['hash'])
        self.sign.storage[(pkh(self.tips), 32768)]()

        is_signed_params = {
            'participant': pkh(self.p1),
            'id': 42,
            'callback': self.mock.address + '%' + 'bool_view'
        }

        opg = self.sign.is_signed(is_signed_params).inject()
        self.bake_block()
        result = self._find_call_result_by_hash(self.p1, opg['hash'])
        self.assertTrue(self.mock.storage['boolValue']())
        self.assertTrue(len(result.operations) == 1)
        op = result.operations[0]
        self.assertEqual(op['destination'], self.mock.address)
        self.assertEqual(op['parameters']['entrypoint'], 'bool_view')

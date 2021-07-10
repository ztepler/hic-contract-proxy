from pytezos.sandbox.node import SandboxedNodeTestCase
from pytezos.sandbox.parameters import sandbox_addresses, sandbox_commitment
from pytezos import ContractInterface, pytezos
from pytezos.contract.result import ContractCallResult
from pytezos.rpc.errors import MichelsonError
import unittest
from os.path import dirname, join
import json
import codecs


def str_to_hex_bytes(string):
    return codecs.encode(string.encode("ascii"), "hex")


FACTORY_TZ = '../build/tz/factory.tz'

LAMBDA_CALLS = {
    'hic_mint_OBJKT': '../build/tz/lambdas/call/hic_mint_OBJKT.tz'
}

LAMBDA_ORIGINATE = {
    'hic_proxy': '../build/tz/lambdas/originate/hic_proxy.tz',
    'basic_proxy': '../build/tz/lambdas/originate/basic_proxy.tz'
}

PACKER_TZ = '../build/tz/packer.tz'
CONTRACTS_DIR = 'contracts'

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


class ContractInteractionsBaseTestCase(SandboxedNodeTestCase):


    def _deploy_contract(self, client, contract, storage):
        """ Deploys contract with given storage """

        # TODO: try to replace key with client.key:
        opg = contract.using(shell=self.get_node_url(), key=client.key)
        opg = opg.originate(initial_storage=storage)

        return opg.fill().sign().inject()


    def _deploy_factory(
        self, client, minter_address, marketplace_address,
        registry_address, token_address):

        factory = ContractInterface.from_file(join(dirname(__file__), FACTORY_TZ))
        factory_init = {
            'data': {
                'minterAddress': minter_address,
                'marketplaceAddress': marketplace_address,
                'registryAddress': registry_address,
                'tokenAddress': token_address
            },
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

        # Deploying factory:
        opg = self._deploy_factory(
            self.p1,
            self.minter.address,
            self.marketplace.address,
            self.registry.address,
            self.objkts.address)

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

        # Loading lambdas:
        def load_lambda(filename):
            return open(join(dirname(__file__), filename)).read()

        self.lambdas = {
            lambda_name: load_lambda(filename)
            for lambda_name, filename in LAMBDA_CALLS.items()
        }

        # Deploying packer (I feel this is temporal solution but who knows):
        #    (it is just used to pack data)
        packer = ContractInterface.from_file(join(dirname(__file__), PACKER_TZ))
        opg = self._deploy_contract(self.p1, packer, 0)
        self.bake_block()
        self.packer = self._find_contract_by_hash(self.p1, opg['hash'])


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

from pytezos.sandbox.node import SandboxedNodeTestCase
from pytezos.sandbox.parameters import sandbox_addresses, sandbox_commitment
from pytezos import ContractInterface, pytezos, MichelsonRuntimeError
from pytezos.contract.result import ContractCallResult
import unittest
from os.path import dirname, join
import json


FACTORY_TZ = '../build/tz/factory.tz'
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


class ContractInteractionsTestCase(SandboxedNodeTestCase):


    def _deploy_contract(self, client, contract, storage):
        """ Deploys contract with given storage """

        # TODO: try to replace key with client.key:
        opg = contract.using(shell=self.get_node_url(), key=client.key)
        opg = opg.originate(initial_storage=storage)

        return opg.fill().sign().inject()


    def _deploy_factory(self, client, minter_address):

        factory = ContractInterface.from_file(join(dirname(__file__), FACTORY_TZ))
        factory_init = {
            'originatedContracts': 0,
            'hicetnuncMinterAddress': minter_address
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


    def _deploy_hic_contracts(self, client):

        # Deploying OBJKTs:
        storage = read_storage('objkts')
        storage.update({'administrator': pkh(client)})
        opg = self._deploy_contract(
            client=client,
            contract=read_contract('objkts'),
            storage=storage)

        self.bake_block()
        self.objkts = self._find_contract_by_hash(client, opg['hash'])

        # Deploying hDAO:
        opg = self._deploy_contract(
            client=client,
            contract=read_contract('objkts'),
            storage=read_storage('objkts'))

        self.bake_block()
        self.hdao = self._find_contract_by_hash(client, opg['hash'])

        # Deploying curate:
        storage = read_storage('curate')
        storage.update({
            'manager': pkh(client) 
        })

        opg = self._deploy_contract(
            client=client,
            contract=read_contract('curate'),
            storage=storage)

        self.bake_block()
        self.curate = self._find_contract_by_hash(client, opg['hash'])

        # Deploying minter:
        storage = read_storage('minter')
        storage.update({
            'curate': self.curate.address,
            'hdao': self.hdao.address,
            'objkt': self.objkts.address,
            'manager': pkh(client) 
        })
        opg = self._deploy_contract(
            client=client,
            contract=read_contract('minter'),
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

        # configure objkts:
        self.objkts.set_administrator(self.minter.address).inject()
        self.bake_block()


    def setUp(self):
        self._activate_accs()
        self._deploy_hic_contracts(self.hic_admin)

        # Deploying factory:
        opg = self._deploy_factory(self.p1, self.minter.address)
        self.bake_block()
        self.factory = self._find_contract_by_hash(self.p1, opg['hash'])

        # Creating contract using proxy
        originate_params = {
            pkh(self.p1):   {'share': 330, 'isCore': True},
            pkh(self.p2):   {'share': 500, 'isCore': True},
            pkh(self.tips): {'share': 170, 'isCore': False}
        }

        opg = self.factory.default(originate_params).inject()
        self.bake_block()
        self.collab = self._find_contract_internal_by_hash(self.p1, opg['hash'])


    def test_withdraw_tokens(self):
        # 1. collab mints, then not admin withdraws: failure
        mint_params = {
            'address': self.collab.address,
            'amount': 1,
            'metadata': '697066733a2f2f516d5952724264554578587269473470526679746e666d596b664a4564417157793632683746327771346b517775',
            'royalties': 250
        }

        opg = self.collab.mint_OBJKT(mint_params).inject()
        self.bake_block()
        result = self._find_call_result_by_hash(self.p1, opg['hash'])

        # 2. collab mints, then admin withdraws: success
        # 3. someone mints, then not admin withdraws: failure
        # 4. someone mints, then admin withdraws: success
        # withdraw zero tokens?
        pass


    '''
    def test_created_contract_params(self):
        pass
        # TODO: test contract created params is equal to expected
        # TODO: test mint/swap/cancel and others?


    def test_reading_views(self):
        pass
        # TODO: test reading views from another contract

    def test_signature_communications(self):
        pass
        # TODO: test all signature contract communications
    '''

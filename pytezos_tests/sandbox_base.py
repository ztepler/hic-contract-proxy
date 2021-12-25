from pytezos.sandbox.node import SandboxedNodeTestCase
from pytezos.sandbox.parameters import sandbox_addresses, sandbox_commitment
from pytezos import ContractInterface, pytezos, MichelsonRuntimeError
from pytezos.contract.result import ContractCallResult
from pytezos.rpc.errors import MichelsonError
import unittest
from os.path import dirname, join
import json
from test_data import CONTRACTS_DIR, FACTORY_FN, SWAP_ADMIN_FN


def pkh(client):
    return client.key.public_key_hash()


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

        opg = contract.using(shell=client.shell, key=client.key)
        opg = opg.originate(initial_storage=storage)

        return opg.send()


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


    def _deploy_swap_admin(
            self, client, gallery_address, token_address, marketplace_address):

        swap_admin = ContractInterface.from_file(join(dirname(__file__), SWAP_ADMIN_FN))
        swap_admin_init = {
            'administrator': pkh(client),
            'galleryAddress': gallery_address,
            'tokenAddress': token_address,
            'marketplaceAddress': marketplace_address
        }

        return self._deploy_contract(client, swap_admin, swap_admin_init)


    def _find_call_result_by_hash(self, client, opg_hash):

        # Get injected operation and convert to ContractCallResult
        opg = client.shell.blocks['head':].find_operation(opg_hash)
        return ContractCallResult.from_operation_group(opg)[0]


    def _load_contract(self, client, contract_address):

        # Load originated contract from blockchain
        contract = client.contract(contract_address)
        contract = contract.using(
            shell=self.client,
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

        # Using two names for the same key:
        self.hic_admin = self.client.using(key='bootstrap4')
        self.admin = self.client.using(key='bootstrap4')
        self.hic_admin.reveal()

        self.buyer = self.client.using(key='bootstrap5')
        self.buyer.reveal()


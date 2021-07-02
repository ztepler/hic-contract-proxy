from pytezos.sandbox.node import SandboxedNodeTestCase
from pytezos.sandbox.parameters import sandbox_addresses, sandbox_commitment
from pytezos import ContractInterface, pytezos, MichelsonRuntimeError
from pytezos.contract.result import ContractCallResult
import unittest
from os.path import dirname, join
import json


FACTORY_TZ = '../build/tz/lambda_factory.tz'
MINT_OBJKT_CALL_CODE = '../build/tz/lambdas/hic_mint_OBJKT.tz'
CREATE_PROXY_CODE = '../build/tz/lambdas/create_proxy.tz'

# PACKER_TZ = '../build/tz/packer.tz'
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
            'data': {
                'originatedContracts': 0,
                'hicetnuncMinterAddress': minter_address,
            },
            'lambdas': {},
            'contracts': {}
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


    def _add_operator(self, contract, owner_client, operator, token_id):
        fa2_contract = owner_client.contract(contract.address)
        update_operatiors_params = [{
            'add_operator': {
                'owner': pkh(owner_client),
                'operator': operator,
                'token_id': token_id}
        }]

        return fa2_contract.update_operators(update_operatiors_params).inject()


    def setUp(self):
        self._activate_accs()
        self._deploy_hic_contracts(self.hic_admin)

        # Deploying factory:
        opg = self._deploy_factory(self.p1, self.minter.address)
        self.bake_block()
        self.factory = self._find_contract_by_hash(self.p1, opg['hash'])

        """
        # Deploying packer (I feel this is temporal solution but who knows):
        #    (it is just used to pack data)
        packer = ContractInterface.from_file(join(dirname(__file__), PACKER_TZ))
        opg = self._deploy_contract(self.p1, packer, 0)
        self.bake_block()
        self.packer = self._find_contract_by_hash(self.p1, opg['hash'])
        """


    '''
    def test_mint_token(self):
        # Creating contract using proxy
        originate_params = {
            pkh(self.p1):   {'share': 330, 'isCore': True},
            pkh(self.p2):   {'share': 500, 'isCore': True},
            pkh(self.tips): {'share': 170, 'isCore': False}
        }

        opg = self.factory.default(originate_params).inject()
        self.bake_block()
        self.collab = self._find_contract_internal_by_hash(self.p1, opg['hash'])

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

        # swap:
        swap_params = {
            'objkt_amount': 4,
            'objkt_id': 0,
            'xtz_per_objkt': 1_000_000,
        }

        swap_id = self.minter.storage['swap_id']()
        opg = self.collab.swap(swap_params).inject()
        self.bake_block()
        result = self._find_call_result_by_hash(self.p1, opg['hash'])

        # collect:
        collect_params = {
            'objkt_amount': 3,
            'swap_id': swap_id
        }
        opg = self.buyer.contract(self.minter.address).collect(
            collect_params).with_amount(3_000_000).inject()

        self.bake_block()
        result = self._find_call_result_by_hash(self.p1, opg['hash'])

        # checking objkt holders:
        self.assertEqual(self.objkts.storage['all_tokens'](), 1)
        self.assertEqual(self.objkts.storage['ledger'][self.collab.address, 0](), 6)
        self.assertEqual(self.objkts.storage['ledger'][self.minter.address, 0](), 1)
        self.assertEqual(self.objkts.storage['ledger'][pkh(self.buyer), 0](), 3)

        # TODO: checking distribution:
        pass
    '''

    def test_marketplace_communication(self):

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
        self._add_operator(self.objkts, self.p1, self.marketplace.address, 0)
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
        collect_params = {
            'objkt_amount': 1,
            'swap_id': swap_id
        }
        opg = self.buyer.contract(self.marketplace.address).collect(
            collect_params).with_amount(1_000_000).inject()

        self.bake_block()
        result = self._find_call_result_by_hash(self.p1, opg['hash'])
        assert self.objkts.storage['ledger'][(pkh(self.buyer), 0)]() == 1

        # reswap this one objkt with low price:
        self._add_operator(self.objkts, self.buyer, self.marketplace.address, 0)
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

        # trying to buy with low-price swap but more that in the swap:
        collect_params = {
            'objkt_amount': 10,
            'swap_id': swap_id
        }

        # This should raise error, because there are only 1 item in swap,
        # but there are no error!:
        opg = self.p2.contract(self.marketplace.address).collect(
            collect_params).with_amount(10*100).inject()
        self.bake_block()

        # and p2 should not receive this 10 objkts:
        assert self.objkts.storage['ledger'][(pkh(self.p2), 0)]() == 10

        result = self._find_call_result_by_hash(self.p1, opg['hash'])


    def test_lambda_proxy(self):

        # Adding contracts to factory:
        create_proxy_lambda = open(
            join(dirname(__file__), CREATE_PROXY_CODE)).read()

        self.factory.add_contract({
            'name': 'proxy_lambda_v1',
            'contract': create_proxy_lambda
        }).inject()
        self.bake_block()

        # Adding lambdas to factory:
        mint_objkt_lambda = open(
            join(dirname(__file__), MINT_OBJKT_CALL_CODE)).read()

        self.factory.add_lambda({
            'name': 'hen_mint_objkt_v1',
            'lambda': mint_objkt_lambda
        }).inject()
        self.bake_block()

        # Creating contract using proxy
        participants = {
            pkh(self.p1):   {'share': 330, 'isCore': True},
            pkh(self.p2):   {'share': 500, 'isCore': True},
            pkh(self.tips): {'share': 170, 'isCore': False}
        }

        originate_params = {
            'participants': participants,
            'contractName': 'proxy_lambda_v1'
        }

        opg = self.factory.create_proxy(originate_params).inject()
        self.bake_block()
        self.collab = self._find_contract_internal_by_hash(self.p1, opg['hash'])

        # Calling execute:
        execute_params = {
            'lambdaName': 'hen_mint_objkt_v1',
            'params': '05070707070a00000016013116e679766d18239f246ca78b0a4fdaa637ecf20000a40107070a00000035697066733a2f2f516d5952724264554578587269473470526679746e666d596b664a4564417157793632683746327771346b517775008803',
            'proxy': self.collab.address
        }

        opg = self.factory.execute_proxy(execute_params).inject()
        self.bake_block()
        result = self._find_call_result_by_hash(self.p1, opg['hash'])

        # TODO: testing running lambda with name that does not exist failed
        # TODO: testing running lambda on proxy-contract not from factory failed
        # TODO: testing that only admin can add lambda/contracts
        # TODO: testing that ids are correctly updates

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
        pass
        # NEED TO UNDERSTAND WHY THESE LINES ARE FAILING:
        """
        # Creating contract using proxy
        originate_params = {
            pkh(self.p1):   {'share': 330, 'isCore': True},
            pkh(self.p2):   {'share': 500, 'isCore': True},
            pkh(self.tips): {'share': 170, 'isCore': False}
        }

        opg = self.factory.default(originate_params).inject()
        self.bake_block()
        self.collab = self._find_contract_internal_by_hash(self.p1, opg['hash'])

        # TODO: test all signature contract communications
        """
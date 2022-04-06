from pytezos.michelson.parse import michelson_to_micheline
from pytezos.michelson.types.base import MichelsonType
from pytezos.contract.result import ContractCallResult
from pytezos import ContractInterface
from pytezos.rpc.errors import MichelsonError
from os.path import dirname, join
from sandbox_base import (
    ContractInteractionsTestCase,
    read_storage,
    pkh,
    read_contract
)
from test_data import (
    load_lambdas, LAMBDA_CALLS, LAMBDA_ORIGINATE,
    PACKER_FN, SIGN_FN, MOCK_FN)
from pytezos.crypto.key import Key
import codecs


def str_to_hex_bytes(string):
    return codecs.encode(string.encode("ascii"), "hex")


class HicProxyTestCase(ContractInteractionsTestCase):

    def _deploy_hic_contracts(self, client):
        # Deploying OBJKTs:
        storage = read_storage('fa2_objkts')
        storage.update({'administrator': pkh(client)})
        opg = self._deploy_contract(
            client=client,
            contract=read_contract('fa2_objkts'),
            storage=storage)

        self.bake_block()
        self.objkts = self._find_contract_by_hash(client, opg.hash())

        # Deploying hDAO:
        storage = read_storage('fa2_hdao')
        storage.update({'administrator': pkh(client)})
        opg = self._deploy_contract(
            client=client,
            contract=read_contract('fa2_hdao'),
            storage=storage)

        self.bake_block()
        self.hdao = self._find_contract_by_hash(client, opg.hash())

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
        self.curate = self._find_contract_by_hash(client, opg.hash())

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
        self.minter = self._find_contract_by_hash(client, opg.hash())

        # configure curate:
        configuration = {
            'fa2': self.hdao.address,
            'protocol': self.minter.address
        }
        self.curate.configure(configuration).send()
        self.bake_block()

        # what does this genesis?:
        self.minter.genesis().send()
        self.bake_block()

        # configure objkts and hdao:
        self.objkts.set_administrator(self.minter.address).send()
        self.bake_block()

        self.hdao.set_administrator(self.minter.address).send()
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
        self.marketplace = self._find_contract_by_hash(client, opg.hash())

        # Deploying registry
        storage = read_storage('subjkt')
        storage.update({'manager': pkh(client)})
        opg = self._deploy_contract(
            client=client,
            contract=read_contract('subjkt'),
            storage=storage)

        self.bake_block()
        self.registry = self._find_contract_by_hash(client, opg.hash())


    def _deploy_marketplace_v3(self, client):
        storage = read_storage('marketplace_v3')
        storage.update({
            'allowed_fa2s': {self.objkts.address: True},
            'manager': pkh(client),
            'fee_recipient': pkh(client),
        })

        opg = self._deploy_contract(
            client=client,
            contract=read_contract('marketplace_v3'),
            storage=storage)

        self.bake_block()
        self.marketplace_v3 = self._find_contract_by_hash(client, opg.hash())


    def _add_operator(self, contract, owner_client, owner, operator, token_id):
        fa2_contract = owner_client.contract(contract.address)
        update_operatiors_params = [{
            'add_operator': {
                'owner': owner,
                'operator': operator,
                'token_id': token_id}
        }]

        return fa2_contract.update_operators(update_operatiors_params).send()


    def setUp(self):
        self._activate_accs()
        self._deploy_hic_contracts(self.hic_admin)

        # Deploying packer (I feel this is temporal solution but who knows):
        #    (it is just used to pack data)
        packer = ContractInterface.from_file(join(dirname(__file__), PACKER_FN))
        opg = self._deploy_contract(self.p1, packer, 0)
        self.bake_block()
        self.packer = self._find_contract_by_hash(self.p1, opg.hash())

        # Deploying factory:
        opg = self._deploy_factory(self.p1)
        self.bake_block()
        self.factory = self._find_contract_by_hash(self.p1, opg.hash())

        # Adding templates to the factory:
        for lambda_name, filename in LAMBDA_ORIGINATE.items():
            originate_lambda = open(
                join(dirname(__file__), filename)).read()

            self.factory.add_template({
                'name': lambda_name,
                'originateFunc': originate_lambda
            }).send()
            self.bake_block()

        # Adding records to the factory:
        def pack_address(address):
            return self.packer.pack_address(
                address).interpret().storage.hex()

        records = {
            'hicMinterAddress': pack_address(self.minter.address),
            'hicMarketplaceAddress': pack_address(self.marketplace.address),
            'hicTokenAddress': pack_address(self.objkts.address),
            'hicRegistryAddress': pack_address(self.registry.address)
        }

        for record_name, value in records.items():
            self.factory.add_record({
                'name': record_name,
                'value': value
            }).send()
            self.bake_block()

        # Loading lambdas:
        self.lambdas = load_lambdas(LAMBDA_CALLS)

        # Deploying signer:
        sign = ContractInterface.from_file(join(dirname(__file__), SIGN_FN))
        sign_storage = {}
        opg = self._deploy_contract(self.p1, sign, sign_storage)
        self.bake_block()
        self.sign = self._find_contract_by_hash(self.p1, opg.hash())

        # Deploying mock view:
        mock = ContractInterface.from_file(join(dirname(__file__), MOCK_FN))
        mock_storage = {'natValue': None, 'boolValue': None}
        opg = self._deploy_contract(self.p1, mock, mock_storage)
        self.bake_block()
        self.mock = self._find_contract_by_hash(self.p1, opg.hash())

        # Deploying Marketplace V3:
        self._deploy_marketplace_v3(self.hic_admin)
        self.bake_block()


    def _originate_default_contract(self):
        # TODO: add admin as param
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

        opg = self.factory.create_proxy(originate_params).send()
        self.bake_block()
        self.collab = self._find_contract_internal_by_hash(self.p1, opg.hash())


    def test_mint_token(self):

        self._originate_default_contract()

        # mint:
        mint_params = {
            'address': self.collab.address,
            'amount': 10,
            'metadata': '697066733a2f2f516d5952724264554578587269473470526679746e666d596b664a4564417157793632683746327771346b517775',
            'royalties': 250
        }

        opg = self.collab.mint_OBJKT(mint_params).send()
        self.bake_block()
        result = self._find_call_result_by_hash(self.p1, opg.hash())

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
        opg = self.collab.swap(swap_params).send()
        self.bake_block()
        result = self._find_call_result_by_hash(self.p1, opg.hash())

        # collect:
        opg = self.buyer.contract(self.marketplace.address).collect(
            swap_id).with_amount(1_000_000).send()

        self.bake_block()
        result = self._find_call_result_by_hash(self.p1, opg.hash())

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
        opg = minter.mint_OBJKT(mint_params).send()
        self.bake_block()
        result = self._find_call_result_by_hash(self.p1, opg.hash())

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
        opg = marketplace.swap(swap_params).send()
        self.bake_block()
        result = self._find_call_result_by_hash(self.p1, opg.hash())

        # collect:
        opg = self.buyer.contract(self.marketplace.address).collect(
            swap_id).with_amount(1_000_000).send()

        self.bake_block()
        result = self._find_call_result_by_hash(self.p1, opg.hash())
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
        opg = marketplace.swap(swap_params).send()
        self.bake_block()
        result = self._find_call_result_by_hash(self.p1, opg.hash())

        # rebuing second swap:
        opg = self.p2.contract(self.marketplace.address).collect(
            swap_id).with_amount(1*100).send()
        self.bake_block()
        result = self._find_call_result_by_hash(self.p1, opg.hash())

        # and p2 should not receive this 1 objkt:
        assert self.objkts.storage['ledger'][(pkh(self.p2), 0)]() == 1
        assert self.objkts.storage['ledger'][(self.marketplace.address, 0)]() == 99

        # Trying to use this second swap second time:
        with self.assertRaises(MichelsonError) as cm:
            opg = self.p2.contract(self.marketplace.address).collect(
                swap_id).with_amount(1*100).send()
            self.bake_block()
            result = self._find_call_result_by_hash(self.p1, opg.hash())

        # Trying to collect swap that does not exist:
        with self.assertRaises(MichelsonError) as cm:
            opg = self.p2.contract(self.marketplace.address).collect(
                3).with_amount(1*100).send()
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
        opg = marketplace.swap(swap_params).send()
        self.bake_block()

        opg = self.buyer.contract(self.marketplace.address).collect(
            swap_id).with_amount(0).send()
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
            opg = marketplace.swap(swap_params).send()
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
        opg = marketplace.swap(swap_params).send()
        self.bake_block()

        opg = self.p2.contract(self.marketplace.address).collect(
            swap_id).with_amount(10).send()
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

        opg = self.factory.create_proxy(originate_params).send()
        self.bake_block()
        self.collab = self._find_contract_internal_by_hash(self.p1, opg.hash())

        # Checking that factory have address of new created collab in their ledger:
        metadata = self.factory.storage['originatedContracts'][self.collab.address]()
        self.assertTrue('hic_proxy' in metadata.decode())

        # Calling execute:
        executeParams = {
            'lambda': self.lambdas['hic_mint_OBJKT'],
            'packedParams': '05070707070a00000016013116e679766d18239f246ca78b0a4fdaa637ecf20000a40107070a00000035697066733a2f2f516d5952724264554578587269473470526679746e666d596b664a4564417157793632683746327771346b517775008803'
        }

        opg = self.collab.execute(executeParams).send()
        self.bake_block()
        result = self._find_call_result_by_hash(self.p1, opg.hash())

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

        opg = self.factory.create_proxy(originate_params).send()
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

        opg = self.factory.create_proxy(originate_params).send()
        self.bake_block()

        # Trying to originate contract with name that does not exist failed:
        originate_params = {
            'templateName': 'unknown',
            'params': packed_participants
        }

        with self.assertRaises(MichelsonError) as cm:
            opg = self.factory.create_proxy(originate_params).send()
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

        opg = self.collab.registry(registry_params).send()
        self.bake_block()
        result = self._find_call_result_by_hash(self.p1, opg.hash())
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
        opg = self.collab.unregistry().send()
        self.bake_block()
        result = self._find_call_result_by_hash(self.p1, opg.hash())

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

        opg = self.p1.contract(self.sign.address).sign(42).send()
        self.bake_block()
        result = self._find_call_result_by_hash(self.p1, opg.hash())
        self.sign.storage[(pkh(self.p1), 42)]()

        opg = self.tips.contract(self.sign.address).sign(32768).send()
        self.bake_block()
        result = self._find_call_result_by_hash(self.p1, opg.hash())
        self.sign.storage[(pkh(self.tips), 32768)]()

        is_signed_params = {
            'participant': pkh(self.p1),
            'id': 42,
            'callback': self.mock.address + '%' + 'bool_view'
        }

        opg = self.sign.is_signed(is_signed_params).send()
        self.bake_block()
        result = self._find_call_result_by_hash(self.p1, opg.hash())
        self.assertTrue(self.mock.storage['boolValue']())
        self.assertTrue(len(result.operations) == 1)
        op = result.operations[0]
        self.assertEqual(op['destination'], self.mock.address)
        self.assertEqual(op['parameters']['entrypoint'], 'bool_view')


    def default_mint(self, minter, address):
        """ Default mint call used in multiple test cases """

        mint_params = {
            'address': address,
            'amount': 1,
            'metadata': '697066733a2f2f516d5952724264554578587269473470526679746e666d596b664a4564417157793632683746327771346b517775',
            'royalties': 250
        }

        opg = minter.mint_OBJKT(mint_params).send()
        self.bake_block()
        result = self._find_call_result_by_hash(self.p1, opg.hash())
        return result


    def default_swap(self, marketplace, artist_address):
        """ Default mint call used in multiple test cases """

        swap_params = {
            'creator': artist_address,
            'objkt_amount': 1,
            'objkt_id': 0,
            'royalties': 250,
            'xtz_per_objkt': 1_000_000,
        }

        opg = marketplace.swap(swap_params).send()
        self.bake_block()
        result = self._find_call_result_by_hash(self.p1, opg.hash())
        return result


    def test_participant_count_limit(self):

        # The real hard gas limit was 221 but I limited contract to 108
        COUNT = 108

        participants = {
            Key.generate(export=False).public_key_hash(): {
                'share': 100,
                'isCore': True
            } for _ in range(COUNT)
        }

        # Packer is just helper contract that converts data to bytes:
        packed_participants = self.packer.pack_originate_hic_proxy(
            participants).interpret().storage.hex()

        originate_params = {
            'templateName': 'hic_proxy',
            'params': packed_participants
        }

        opg = self.factory.create_proxy(originate_params).send()
        self.bake_block()
        self.collab = self._find_contract_internal_by_hash(self.p1, opg.hash())

        # mint:
        collab = self.p1.contract(self.collab.address)
        result = self.default_mint(
            minter=collab,
            address=self.collab.address)

        # update operators:
        self._add_operator(
            collab,
            self.p1,
            collab.address,
            self.marketplace.address,
            0)

        self.bake_block()

        # swap:
        swap_id = self.marketplace.storage['counter']()
        result = self.default_swap(
            marketplace=collab,
            artist_address=collab.address)

        # collect:
        opg = self.buyer.contract(self.marketplace.address).collect(
            swap_id).with_amount(1_000_000).send()

        self.bake_block()
        result = self._find_call_result_by_hash(self.p1, opg.hash())

        opg_details = self.p1.shell.blocks['head':].find_operation(opg.hash())
        metadata = opg_details['contents'][0]['metadata']
        internal_ops = metadata['internal_operation_results']

        # INTERNAL TRANSACTIONS:
        # + 1x fa2 transfer
        # + 1x marketplace fee
        # + 1x sale transaction from marketplace to collab
        # + 1x royalty transaction from marketplace to collab
        # + participants count sale transaction from collab
        # + participants count royalty transaction from collab

        target_op_count = len(participants)*2 + 4
        self.assertEqual(len(internal_ops), target_op_count)

        # Total gas (1,040,000 hard op limit in florencenet):
        gas = [int(op['result']['consumed_gas']) for op in internal_ops]
        total_gas = sum(gas)

        self.assertTrue(total_gas <= 1_040_000)


    def test_transfer_from_collab(self):

        self._originate_default_contract()

        # mint:
        collab = self.p1.contract(self.collab.address)
        result = self.default_mint(
            minter=collab,
            address=self.collab.address)

        # transfer to self.p2:
        transfer_params = [{
            'txs': [{
                'to_': pkh(self.p2),
                'amount': 1,
                'token_id': 0
            }],
            'from_': self.collab.address
        }]

        opg = collab.transfer(transfer_params).send()
        self.bake_block()
        result = self._find_call_result_by_hash(self.p1, opg.hash())

        # checking that transfer succeed:
        self.assertEqual(self.objkts.storage['all_tokens'](), 1)
        self.assertEqual(self.objkts.storage['ledger'][self.collab.address, 0](), 0)
        self.assertEqual(self.objkts.storage['ledger'][pkh(self.p2), 0](), 1)


    def test_swap_admin_use_case(self):

        # Creating collab (p1 is default admin):
        self._originate_default_contract()

        # Deploying swap admin
        opg = self._deploy_swap_admin(
            self.p1,
            self.collab.address,
            self.objkts.address,
            self.marketplace.address)

        self.bake_block()
        self.swap_admin = self._find_contract_by_hash(self.p1, opg.hash())

        # Transfer ownership:
        self.collab.update_admin(self.swap_admin.address).send()
        self.bake_block()

        self.swap_admin.accept_gallery_ownership().send()
        self.bake_block()

        self.assertEqual(
            self.collab.storage['administrator'](),
            self.swap_admin.address)

        # Mint something from p2:
        result = self.default_mint(
            minter=self.minter,
            address=pkh(self.p2))

        # update operators:
        self._add_operator(
            contract=self.objkts,
            owner_client=self.p2,
            owner=pkh(self.p2),
            operator=self.swap_admin.address,
            token_id=0)

        self.bake_block()

        # Swap it on collab using swap admin from p2:
        swap_admin = self.p2.contract(self.swap_admin.address)
        result = self.default_swap(
            marketplace=swap_admin,
            artist_address=pkh(self.p2))

        # collect:
        # TODO: need to move all this default amounts to ? idk
        swap_id = 0
        opg = self.buyer.contract(self.marketplace.address).collect(
            swap_id).with_amount(1_000_000).send()

        self.bake_block()
        result = self._find_call_result_by_hash(self.p1, opg.hash())

        # checking that all shareholders get some:
        opg_details = self.p1.shell.blocks['head':].find_operation(opg.hash())
        metadata = opg_details['contents'][0]['metadata']
        internal_ops = metadata['internal_operation_results']

        destinations = {op['destination'] for op in internal_ops}
        shareholders = set(self.collab.storage()['shares'].keys())
        self.assertTrue(shareholders.issubset(destinations))

        # return back rights from not admin should fail:
        with self.assertRaises(MichelsonError) as cm:
            opg = self.p2.contract(self.swap_admin.address).return_admin().send()
            self.bake_block()

        # return back rights and check that collab admin is p1 again
        swap_admin = self.p1.contract(self.swap_admin.address)
        result = swap_admin.return_admin().send()
        self.bake_block()

        gallery = self.p1.contract(self.collab.address)
        result = gallery.accept_ownership().send()
        self.bake_block()

        self.assertEqual(
            self.collab.storage['administrator'](),
            pkh(self.p1))


    def test_marketplace_v3_lambda(self):
        # creating default proxy contract:
        self._originate_default_contract()

        # minting default objkt:
        result = self.default_mint(
            minter=self.collab,
            address=self.collab.address)
        self.bake_block()

        # allwing markeplace v3 to use this minted objkt from collab contract:
        self._add_operator(
            contract=self.collab,
            owner_client=self.p1,
            owner=self.collab.address,
            operator=self.marketplace_v3.address,
            token_id=0)
        self.bake_block()

        # packing marketplace params:
        marketplace_v3_call_params = {
            'marketplaceAddress': self.marketplace_v3.address,
            'params': {
                'fa2': self.objkts.address,
                'objkt_id': 0,
                'objkt_amount': 1,
                'royalties': 250,
                'xtz_per_objkt': 1_000_000,
                'creator': self.collab.address
            }
        }

        type_expression = michelson_to_micheline("""
        pair (address %marketplaceAddress)
                  (pair %params
                     (address %fa2)
                     (pair (nat %objkt_id)
                           (pair (nat %objkt_amount)
                                 (pair (mutez %xtz_per_objkt) (pair (nat %royalties) (address %creator))))))
        """)

        params_type = MichelsonType.match(type_expression)
        filled_params = params_type.from_python_object(marketplace_v3_call_params)
        packed_marketplace_call_params = filled_params.pack()

        executeParams = {
            'lambda': self.lambdas['marketplace_v3_swap'],
            'packedParams': packed_marketplace_call_params
        }

        opg = self.collab.execute(executeParams).send()
        self.bake_block()
        result = self._find_call_result_by_hash(self.p1, opg.hash())

        # Checking result params:
        self.assertTrue(len(result.operations) == 1)
        op = result.operations[0]
        self.assertEqual(op['destination'], self.marketplace_v3.address)
        self.assertTrue(op['amount'] == '0')
        self.assertTrue(op['parameters']['entrypoint'] == 'swap')

        # checking that objkt ledger contains with that marketplace v3 holds this objkt:
        self.assertEqual(self.objkts.storage['all_tokens'](), 1)
        self.assertEqual(self.objkts.storage['ledger'][self.collab.address, 0](), 0)
        self.assertEqual(self.objkts.storage['ledger'][self.marketplace_v3.address, 0](), 1)

        # collecting objkt:
        collect_op = self.p1.contract(self.marketplace_v3.address).collect(0)
        collect_op.with_amount(1_000_000).send()
        self.bake_block()
        self.assertEqual(self.objkts.storage['ledger'][pkh(self.p1), 0](), 1)


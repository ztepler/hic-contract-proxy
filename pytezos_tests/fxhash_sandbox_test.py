from sandbox_base import (
    ContractInteractionsTestCase,
    pkh,
    read_storage,
    read_contract
)
from os.path import join, dirname
from pytezos import ContractInterface


FXHASH_COLLAB_FN = '../build/tz/fxhash_proxy.tz'


class FxHashInteractionsTestCase(ContractInteractionsTestCase):
    def _deploy_fxhash(self, client):

        # Deploying issuer:
        storage = read_storage('fxhash_issuer')
        storage.update({'administrator': pkh(client)})
        opg = self._deploy_contract(
            client=client,
            contract=read_contract('fxhash_issuer'),
            storage=storage)

        self.bake_block()
        self.issuer = self._find_contract_by_hash(client, opg.hash())


    def _deploy_proxy(self, client, issuer_address):

        fxhash_proxy = ContractInterface.from_file(
            join(dirname(__file__), FXHASH_COLLAB_FN))

        fxhash_storage = {
            'administrator': pkh(client),
            'proposedAdministrator': None,
            'shares': {pkh(client): 100},
            'totalShares': 100,
            'issuerAddress': issuer_address,
            'coreParticipants': set(),
            'isPaused': False
        }

        return self._deploy_contract(client, fxhash_proxy, fxhash_storage)


    def setUp(self):
        self._activate_accs()
        self.admin = self.client.using(key='bootstrap4')
        self._deploy_fxhash(self.admin)

        # deploying fxhash proxy:
        opg = self._deploy_proxy(self.admin, self.issuer.address)
        self.bake_block()
        self.fxhash_proxy = self._find_contract_by_hash(self.p1, opg.hash())

    def test_mint_issuer(self):
        mint_params = {
            'amount': 42,
            'enabled': True,
            'metadata': {
                '': '697066733a2f2f516d59644b746b61467279777071446343764d3232663259664a69565369416b72485156635a6679586d554b484b'},
            'price': 1000000,
            'royalties': 100}

        opg = self.admin.contract(self.fxhash_proxy.address).mint_issuer(mint_params).send()
        self.bake_block()
        result = self._find_call_result_by_hash(self.p1, opg.hash())

        ledger_data = self.issuer.storage['ledger'][(self.fxhash_proxy.address, 0)]()
        assert ledger_data['balance'] == 42

        # TODO: trying to mint from issuer
        # TODO: trying to swap
        # TODO: trying to registry using fxhash registry


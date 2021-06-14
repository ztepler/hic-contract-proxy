from pytezos import ContractInterface, pytezos, MichelsonRuntimeError
from unittest import TestCase
from os.path import dirname, join


COLLAB_FN = '../build/tz/contract_proxy_map.tz'
FACTORY_FN = '../build/tz/factory.tz'


class SignsTest(TestCase):

    def setUp(self):
        self.collab = ContractInterface.from_file(join(dirname(__file__), COLLAB_FN))
        self.factory = ContractInterface.from_file(join(dirname(__file__), FACTORY_FN))
        self.p1 = 'tz1iQE8ijR5xVPffBUPFubwB9XQJuyD9qsoJ'
        self.p2 = 'tz1MdaJfWzP5pPx3gwPxfdLZTHW6js9havos'
        self.tips = 'tz1RS9GoEXakf9iyBmSaheLMcakFRtzBXpWE'
        self.admin = self.p1

        self.mint_params = {
            'address': 'KT1VRdyXdMb452GRnSz7tPFQVg96bq2XAmSN',
            'amount': 1,
            'metadata': '697066733a2f2f516d5952724264554578587269473470526679746e666d596b664a4564417157793632683746327771346b517775',
            'royalties': 250
        }

        self.originate_params = {
            'administrator': self.admin,
            'shares': {
                self.p1: 330,
                self.p2: 500,
                self.tips: 170
            },
            'coreParticipants': {self.p1, self.p2},
        }

        self.factory_init = {
            'originatedContracts': 0,
            'hicetnuncMinterAddress': 'KT1Hkg5qeNhfwpKW4fXvq7HGZB9z2EnmCCA9'
        }

        self.result = None
        self.total_incomings = 0


    def _create_collab(self, sender):
        result = self.factory.default(self.originate_params).interpret(
            storage=self.factory_init, sender=sender)
        self.assertEqual(len(result.operations), 1)

        operation = result.operations[0]
        self.assertTrue(operation['kind'] == 'origination')
        self.collab.storage_from_micheline(operation['script']['storage'])
        self.storage = self.collab.storage()


    def _propose_mint(self, sender):
        result = self.collab.mint_OBJKT(self.mint_params).interpret(
            sender=sender,
            storage=self.storage)

        self.assertTrue(len(result.operations) == 0)
        self.storage = result.storage


    def _finalize_mint(self, sender):
        result = self.collab.finalize_mint().interpret(
            sender=sender, storage=self.storage)

        self.assertEqual(len(result.operations), 1)
        self.assertEqual(len(result.storage['signs']), 0)
        self.assertEqual(result.storage['suggestedMint'], None)

        operation = result.operations[0]
        self.assertEqual(operation['destination'], self.factory_init['hicetnuncMinterAddress'])
        self.assertEqual(operation['amount'], '0')
        self.assertEqual(operation['parameters']['entrypoint'], 'mint_OBJKT')

        bytes_metadata = operation['parameters']['value']['args'][1]['bytes']
        metadata = bytearray.fromhex(bytes_metadata).decode()
        self.assertEqual(self.storage['suggestedMint']['metadata'].decode(), metadata)

        self.storage = result.storage


    def _sign(self, participant, params=None):
        params = params or self.mint_params
        result = self.collab.sign(params).interpret(
            sender=participant,
            storage=self.storage)

        self.assertTrue(len(result.operations) == 0)
        self.storage = result.storage

        self.assertTrue(participant in result.storage['signs'])


    def test_signs(self):
        # admin creates contract with 2 core and one tip participant:
        self._create_collab(self.admin)

        # assert that there are no signs:
        self.assertTrue(len(self.collab.storage()['signs']) == 0)

        # participant tries to sign: failure because no mint is proposed:
        with self.assertRaises(MichelsonRuntimeError) as cm:
            self._sign(self.p1)
        self.assertTrue("No mint is proposed" in str(cm.exception))

        # admin propose mint:
        self._propose_mint(self.admin)

        # admin tries to mint: failure because no one signed:
        with self.assertRaises(MichelsonRuntimeError) as cm:
            self._finalize_mint(self.admin)
        self.assertTrue("Can't mint while proposal is not signed" in str(cm.exception))

        # admin signs, tries to mint again: failure because still unsinged p2:
        self._sign(self.p1)
        with self.assertRaises(MichelsonRuntimeError) as cm:
            self._finalize_mint(self.admin)
        self.assertTrue("Can't mint while proposal is not signed" in str(cm.exception))

        # tip tries to sign: failure because he is not core
        with self.assertRaises(MichelsonRuntimeError) as cm:
            self._sign(self.tips)
        self.assertTrue("Sender is not core participant" in str(cm.exception))

        # second core signs with wrong params and failed:
        wrong_params = self.mint_params.copy()
        wrong_params['royalties'] = 100
        with self.assertRaises(MichelsonRuntimeError) as cm:
            self._sign(self.p2, params=wrong_params)
        self.assertTrue("Signing params differ from suggested" in str(cm.exception))

        # second core signs with same-correct params and succeed:
        self._sign(self.p2)

        # admin tries to mint and succeed:
        self._finalize_mint(self.admin)

        # admin tries to mint again and get failure because no proposal:
        with self.assertRaises(MichelsonRuntimeError) as cm:
            self._finalize_mint(self.admin)
        self.assertTrue("Can't mint while proposal is not signed" in str(cm.exception))

        # admin adds new proposal and succeed:
        self._propose_mint(self.admin)

        # assert that all signs is reset:
        self.assertTrue(len(self.collab.storage()['signs']) == 0)

        # admins signs, tries to mint: failure because second participant is not signed
        self._sign(self.p1)
        with self.assertRaises(MichelsonRuntimeError) as cm:
            self._finalize_mint(self.admin)
        self.assertTrue("Can't mint while proposal is not signed" in str(cm.exception))

        # TODO: test:
        # - admin changes proposal
        # - p2 tries to mint and fails
        # - p2 signs new proposal
        # - admin tries to mint and failed because p1 is not signed
        # - p1 signs again

        # second core signs and succeed:
        self._sign(self.p2)

        # admin succesfully mints second contract:
        self._finalize_mint(self.admin)

        # TODO: should no core participants be allowed? Maybe do special test with it
        # - admin creates new contract with no core
        # - admin propose mint and then call mint   

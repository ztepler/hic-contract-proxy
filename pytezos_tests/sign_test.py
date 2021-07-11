from pytezos import MichelsonRuntimeError
from hic_base import HicBaseCase


class SignTest(HicBaseCase):

    def test_signing(self):

        # Check that sign succeed for any artist for any work:
        self.result = self._sign_sign(self.p1, 42)

        # This is very strange, but pytezos failed inside
        # _sign_is_signed with MichelsonRuntimeError "keys are unsorted"
        # if id very big (32000 for example)
        self.result = self._sign_sign(self.tips, 32)

        # Checking is_sign_view for signed works, True case:
        is_signed = self._sign_is_signed(participant=self.p1, objkt_id=42)
        self.assertTrue(is_signed)

        # False case
        is_signed = self._sign_is_signed(participant=self.p1, objkt_id=43)
        self.assertFalse(is_signed)

        # False case 2:
        is_signed = self._sign_is_signed(participant=self.tips, objkt_id=42)
        self.assertFalse(is_signed)

        # Another work from False case is became True case:
        self.result = self._sign_sign(self.p1, 43)
        is_signed = self._sign_is_signed(participant=self.p1, objkt_id=43)
        self.assertTrue(is_signed)

        # Unsign test:
        self.result = self._sign_unsign(self.p1, 43)

        # And again False case:
        is_signed = self._sign_is_signed(participant=self.p1, objkt_id=43)
        self.assertFalse(is_signed)

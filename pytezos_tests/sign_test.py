from pytezos import MichelsonRuntimeError
from hic_base import HicBaseCase


class SignTest(HicBaseCase):

    def test_signing(self):

        # Check that sign succeed for any artist for any work:
        self.result = self._sign_sign(self.p1, 42)
        self.result = self._sign_sign(self.tips, 32768)


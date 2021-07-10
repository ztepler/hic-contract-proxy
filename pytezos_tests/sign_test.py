from pytezos import MichelsonRuntimeError
from hic_base import HicBaseCase


class SignTest(HicBaseCase):

    def test_signing(self):

        self.result = self._sign_sign(self.p1)

from os.path import dirname, join


def load_lambda(filename):
    return open(join(dirname(__file__), filename)).read()

def load_lambdas(lambda_calls):
    return {
        lambda_name: load_lambda(filename)
        for lambda_name, filename in lambda_calls.items()
    }


LAMBDA_CALLS = {
    'hic_mint_OBJKT': '../build/tz/lambdas/call/hic_mint_OBJKT.tz'
}

LAMBDA_ORIGINATE = {
    'hic_proxy': '../build/tz/lambdas/originate/hic_proxy.tz',
    'basic_proxy': '../build/tz/lambdas/originate/basic_proxy.tz'
}

COLLAB_FN = '../build/tz/hic_proxy.tz'
FACTORY_FN = '../build/tz/factory.tz'
SIGN_FN = '../build/tz/sign.tz'
PACKER_FN = '../build/tz/packer.tz'

HIC_PROXY_CODE = '../build/tz/lambdas/originate/hic_proxy.tz'

CONTRACTS_DIR = 'contracts'


DEFAULT_PARAMS = {
    'mint_OBJKT': {
        'address': 'KT1VRdyXdMb452GRnSz7tPFQVg96bq2XAmSN',
        'amount': 1,
        'metadata': '697066733a2f2f516d5952724264554578587269473470526679746e666d596b664a4564417157793632683746327771346b517775',
        'royalties': 250
    }
}


from pytezos import pytezos, ContractInterface
from random import randint

COLLAB_TZ = 'build/tz/hic_proxy.tz'
PARTICIPANTS = 100


def generate_key():
    return pytezos.key.generate(export=False).public_key_hash()


def deploy():
    """ Deploys collab contract with two participants """

    client = pytezos.using(key='ithacanet.json')
    shares = {generate_key(): randint(1, 1000) for _ in range(PARTICIPANTS)}

    storage = {
        'administrator': client.key.public_key_hash(),
        'shares': shares,
        'totalShares': sum(shares.values()),
        'minterAddress': 'KT1Hkg5qeNhfwpKW4fXvq7HGZB9z2EnmCCA9',
        'marketplaceAddress': 'KT1HbQepzV1nVGg8QVznG7z4RcHseD5kwqBn',
        'tokenAddress': 'KT1RJ6PbjHpwc3M5rw5s2Nbmefwbuwbdxton',
        'registryAddress': 'KT1My1wDZHDGweCrJnQJi3wcFaS67iksirvj',
        'coreParticipants': {'tz1PjsbveFyzpTcJ6KkXEjNR1CYr55BGboQv'},
        'isPaused': False,
        'totalReceived': 0,
        'threshold': 0,
        'undistributed': {address: 0 for address in shares},
        'residuals': 0
    }

    contract = ContractInterface.from_file(COLLAB_TZ).using(
        shell=client.shell,
        key=client.key
    )

    opg = contract.originate(initial_storage=storage).send()
    print(f'success: {opg.hash()}')
    client.wait(opg)


if __name__ == '__main__':
    deploy()


from pytezos import pytezos, ContractInterface
COLLAB_TZ = 'build/tz/hic_proxy.tz'


def deploy():
    """ Deploys collab contract with two participants """

    client = pytezos.using(key='ithacanet.json')
    one_address = client.key.public_key_hash()
    another_address = 'tz1dnyX1j91SkCEZxiQNuvSs6zzGhCyVmazx'

    storage = {
        'administrator': one_address,
        'proposedAdministrator': None,
        'shares': {
            one_address: 1000,
            another_address: 10
        },
        'totalShares': 1010,
        'minterAddress': 'KT1Hkg5qeNhfwpKW4fXvq7HGZB9z2EnmCCA9',
        'marketplaceAddress': 'KT1HbQepzV1nVGg8QVznG7z4RcHseD5kwqBn',
        'tokenAddress': 'KT1RJ6PbjHpwc3M5rw5s2Nbmefwbuwbdxton',
        'registryAddress': 'KT1My1wDZHDGweCrJnQJi3wcFaS67iksirvj',
        'coreParticipants': {'tz1PjsbveFyzpTcJ6KkXEjNR1CYr55BGboQv'},
        'isPaused': False,
        'totalReceived': 0,
        'threshold': 0,
        'undistributed': {
            one_address: 0,
            another_address: 0
        }
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


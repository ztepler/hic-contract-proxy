from pytezos import ContractInterface, pytezos, MichelsonRuntimeError
from getpass import getpass
from pytezos.crypto.key import Key
from os.path import join, dirname
# TODO: this is bad dependency:
from pytezos_tests.test_data import LAMBDA_CALLS, LAMBDA_ORIGINATE, load_lambdas, PACKER_FN
from os.path import join, dirname

FACTORY_TZ = join(dirname(__file__), '..', 'build', 'tz', 'factory.tz')
# SHELL = 'https://rpc.tzkt.io/mainnet/'
SHELL = 'https://florence-tezos.giganode.io/'
# edskS4kXzwjfkwfoJ4xdaAjdq9RP56mc34xdmJwtdDqve4aUwBW2K3HjXbGJnpLWzvdepV9Tv2oTK97Ngw66g4PWLTaPiJuAw7

def get_client():
    return pytezos.using(
        key=Key.from_encoded_key(getpass()),
        shell=SHELL
    )


# TODO: use pytezos pack instead, there are some method to do this:
def pack_address(address):
    packer = ContractInterface.from_file(PACKER_FN)
    return packer.pack_address(address).interpret().storage.hex()

MAINNET_ADDRESSES = {
    'hicMinterAddress': pack_address('KT1Hkg5qeNhfwpKW4fXvq7HGZB9z2EnmCCA9'),
    'hicMarketplaceAddress': pack_address('KT1HbQepzV1nVGg8QVznG7z4RcHseD5kwqBn'),
    'hicTokenAddress': pack_address('KT1RJ6PbjHpwc3M5rw5s2Nbmefwbuwbdxton'),
    'hicRegistryAddress': pack_address('KT1My1wDZHDGweCrJnQJi3wcFaS67iksirvj')
}

# TODO: split this in separate functions:
def deploy_factory(client):

    init_storage = {
        'records': {},
        'templates': {},
        'originatedContracts': {},
        'administrator': client.key.public_key_hash(),
        'proposedAdministrator': None
    }

    contract = ContractInterface.from_file(FACTORY_TZ)

    # Factory origination:
    opg = pytezos.origination(
        script=contract.script(initial_storage=init_storage)).send()
    client.wait([opg.hash()], num_blocks_wait=1)

    # Searching for factory address:
    op = client.shell.blocks['head':].find_operation(opg.hash())
    op_result = op['contents'][0]['metadata']['operation_result']
    factory_address = op_result['originated_contracts'][0]

    new_factory = pytezos.contract(factory_address)

    # configuring
    originate_funcs = {
        name: open(filename).read()
        for name, filename in LAMBDA_ORIGINATE.items()
    }

    lambda_calls = load_lambdas(LAMBDA_CALLS)

    add_template_transaction = new_factory.add_template({
        'name': 'hic_proxy',
        'originateFunc': originate_funcs['hic_proxy']}
    ).as_transaction()

    add_records_transactions = [
        new_factory.add_record(dict(name=name, value=value)).as_transaction()
        for name, value in MAINNET_ADDRESSES.items()
    ]

    transactions = [add_template_transaction] + add_records_transactions
    bulk_transactions = pytezos.bulk(*transactions)

    result = bulk_transactions.send()


if __name__ == '__main__':
    client = get_client()
    deploy_factory(client)

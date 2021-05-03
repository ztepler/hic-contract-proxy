### Distributing wealth between multiple collaborators

This is experimental smart contracts collection that aimed to be used with hic et nunc as a "proxy". At the moment there are two contracts in this git that allow to distribute earnings that received by collaborative contract:
1. ContractProxyBigMap: using bigmaps that allows to add a lot of shareholders but it require to call withdraw for each participant.
2. ContractProxyMap: using simple maps and doing all distribution inside Default entrypoint, so there is no need in withdraw method.

Looks like the second approach is easier, at least for small amount of participants. At this moment I am focused only on the second contract (ContractProxyMap).

### NOTE: this contracts is not audited, not well tested, this is just proof of concept. Use it for own risk and fun.

Here you can find forked hicetnunc frontend, that allows you to pick proxy contract by it address and mint/swap objects using it: https://github.com/ztepler/hicetnunc


### Next tasks:
- test factory contract creation (test for different shares option)
- make form in forked h=n frontend that allows to originate new kind of this contract
- need to implement possibility to add / withdraw tokens from contract (it would allow to swap custom tokens and it may be useful for galleries + possibility to add/remove hDAO)
- write little docs
- write more tests
- change administrator method


### Next mad ideas:
- future idea #1: looks like it is possible to make shares as FA2 token and distribute earnings between those who have this token (with Map contract)
- future idea #2: it should be possible to distribute some tokens for every participant that buys something from contract (in the way hDAO airdrop was). Need to test this possibility

----
### Running tests:
1. Install requirements (pytezos + pytest):
```pip install pytezos_tests\requirements.txt```
2. Run tests:
```pytest . -v```

### Example (ContractProxyBigMap):
The first objkt that succeed is https://www.hicetnunc.xyz/objkt/31447

I minted this objkt using originated KT1F12PhZuUavUwesn7eqCaEZ5PZgZDnoC5c smart contract (where I added two mine accounts with 67% and 33% shares between them), then I swapped it and bought by myself for 1tez. After that I called withdrawals from each of my two accs. You can see the interactions on BCD:

https://better-call.dev/mainnet/KT1F12PhZuUavUwesn7eqCaEZ5PZgZDnoC5c/operations


### Example with auto payments (ContractProxyMap):
https://better-call.dev/mainnet/KT1PR98zmCpY8k7Hk1ibwbKi8m94UHMAjHe5/operations


### Factory example (florencenet):
https://better-call.dev/florencenet/KT1ExTWLVt41GBqrs2BhB9aoM317Fkd2wqfW/operations
Created proxy contract with 4 accounts and send here 8xtz: https://better-call.dev/florencenet/opg/op3wwbfwEs81o8JtohSNGdkdujHTC45Af84vNQA2c6yuLh3ZB7k/contents


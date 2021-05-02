### Distributing wealth between multiple collaborators

This is experimental smart contracts collection that aimed to be used with hic et nunc as a "proxy". At the moment there are two contracts in this git that allows to distribute earnings that received by this contract:
1. One using bigmaps that allows to add a lot of shareholders but it require to call withdraw for each participant.
2. Another using simple maps and doing all distribution inside Default entrypoint, so there is no need in withdraw method. Looks like second is more useful for current purposes.

Looks like the second approach is easier, at least for small amount of participants.

NOTE: this contracts is not audited, not well tested, this is just proof of concept. There are no cancel swap entrypoint implemented yet. Use it for own risk and fun.

Here you can find forked hicetnunc frontend, that allows to pick a proxy contract and mint/swap objects using it: https://github.com/ztepler/hicetnunc


### Next tasks:
- need to implement cancel swap and all other entrypoints from h=n
- need to implement possibility to add / withdraw tokens from contract (it would allow to swap custom tokens and it may be useful for galleries)
- write little docs
- need to implement possibility to withdraw any tokens from contract (to withdraw hDAO and to withdraw tokens that are locked inside the contract)
- make simple frontend that allows to originate new kind of this contract
- need to write more tests
- should I replace assert -> assertEqual in the tests?


### Next mad ideas:
- future idea #1: looks like it is possible to make shares as FA2 token and distribute earnings between those who have this token (with Map contract)
- future idea #2: it should be possible to distribute some tokens for every participant that buys something from contract (in the way hDAO airdrop was). Need to test this possibility

----
### Running tests:
1. Install requirements (pytezos + pytest):
```pip install pytezos_tests\requirements.txt```
2. Run tests:
```pytest . -v```

### Example:
The first objkt that succeed is https://www.hicetnunc.xyz/objkt/31447

I minted this objkt using originated KT1F12PhZuUavUwesn7eqCaEZ5PZgZDnoC5c smart contract (where I added two mine accounts with 67% and 33% shares between them), then I swapped it and bought by myself for 1tez. After that I called withdrawals from each of my two accs. You can see the interactions on BCD:

https://better-call.dev/mainnet/KT1F12PhZuUavUwesn7eqCaEZ5PZgZDnoC5c/operations


### Example with auto payments:
https://better-call.dev/mainnet/KT1PR98zmCpY8k7Hk1ibwbKi8m94UHMAjHe5/operations


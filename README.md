plan:

The most important tasks:
- find the way to recreate all IPFS calls and upload some asset and metadata (maybe just find the code from H=N frontend?)
- clean up code, write little docs, publish
- need to implement cancel swap
- need to implement hDAO distribution ?

Possible problems:
- not equal divisions

After contract is ready:
- make simple frontend that allows to mint object using this contract address
- make simple frontend that allows to originate new kind of this contract

Mad ideas:
- future idea #1: is it possible to make shareas as token that have some supply and those who have this token can withdraw their profits from contract? Looks not very easy to achieve because it is not clear how to track which shares are withdrawn and which are not.


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


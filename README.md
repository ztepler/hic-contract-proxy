plan:

The most important tasks:
- need to implement swap 
- find the way to recreate all IPFS calls and upload some asset and metadata (maybe just find the code from H=N frontend?)
- test this contract in mainnet with pair of mine accounts
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


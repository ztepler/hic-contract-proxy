plan:

The most important tasks:
+ test that H=N minter accepting KT address as minter in interpret mode
- prepare truffle project to work with contract
- create simple contract that during origination accepts map / bigmap of address: nat of shares
    - set creator as administrator (who can use this contract to call H=N minter)
- add method to this contract that makes call to H=N minter and creates new objkt using H=N interface
- add method to withdraw profits from contract
- how to track what amounts should be distributed? should it be another method to distribute tokens that received by smart contract? I mean if one takes it share it should be tracked somehow
    1. it is possible to recalculate balances each time withdraw is called, if there are was new incomings
    2. it is possible to keep both accrued value and withdrawn value and each withdraw recalculate withdraw value from caller and accrued values if there was some incomings from the past withdrawals
- test this contract in pytezos to be shure that it is working properly
- need to implement swap and cancel swap too
- need to implement hDAO distribution ?
- find the way to recreate all IPFS calls and upload some asset and metadata (maybe just find the code from H=N frontend?)
- test this contract in mainnet with pair of mine accounts
- clean up code, write little docs, publish

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


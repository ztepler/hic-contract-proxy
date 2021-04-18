Okay, there are two contracts now. One using bigmaps that allows to add a lot of shareholders but it require to call withdraw for each participant. Another using simple maps and doing all distribution inside Default entrypoint, so there is no need in withdraw method. Looks like second is more useful for current purposes.

NOTE: this contracts is not audited, not well tested, this is just proof of concept. There are no cancel swap entrypoint implemented yet. Be carefull if you use it.

Frontend to use this contract (simple forked hic et nunc) would be soon (do I need to host it somewhere to give opportunity to test interactions with it?).

### Next tasks:
- need to write more tests (the contract with map have no test at the moment)
- need to implement cancel swap
- clean up code, write little docs, publish
- need to implement hDAO distribution ?
- make simple frontend that allows to originate new kind of this contract

Possible problems:
- not equal divisions

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


### Example with auto payments:
https://better-call.dev/florencenet/KT1Nja3rA8PofAXrd4mMVyzrsyh6S22rLEFF/operations


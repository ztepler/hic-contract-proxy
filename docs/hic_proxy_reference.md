# Split contract entrypoints:
## default
- Expects `unit` as parameter
- Expects some xtz amount attached to the transaction
- Returns operations with distributed splits to participants
- Changes storage `undistributed` ledger
- Changes storage `residuals` sum
- Anyone can call this entrypoint
- Behaviour depends on `threshold` settings
- Some xtz amount might be locked in `residuals`

This entrypoint allows HicProxy contract to receive xtz and split it among participants. When this contract used as a recepient of xtz (as a seller in the marketplace or as a royalty receiver) it runs logic that redistribute incoming value using participant shares. By default all incoming values automaticly sent to participants, but admin can set threshold that determines the minimal value that will trigger automatic payout to participant. If value is less than threshold it will be kept in contract until it reaches it. If incoming amount can't be split equally between all participants, the residuals left on the contract and will be reused next time contract recieves some payment (during next `default` call).

## withdraw
- Expects `address` of the participant that should receive undistributed amount
- Expects no attached amount
- Returns operation with this undistributed amount from `undistributed` ledger
- Sets `undistributed` ledger for `address` to `0n`
- Anyone can call this entrypoint for any address in `undistributed` ledger

This entrypoint allow participant to withdraw its undistributed earnings if there is some threshold set and participant wants to receive his share before this threshold is reached. Anyone can call this withdraw for anyone, so it is possible to withdraw for a contract if it had no logic to call withdraw by itself, it can be useful for stacked collab contracts.

## set\_threshold
- Expects `nat` with new threshold value
- Expects no attached amount
- Changes storage `threshold` value
- Only admin can call this entrypoint

This entrypoint changes threshold value that used in `default` redistribution mechanics. Default value is `0n` which means no threshold is set.

## execute
- Expects `executeParams` which is record of `lambda` with `executableCall` and `packedParams` with `bytes` payload
- Might allow to attach some amount to the call
- Emits operations that encoded in lambda
- Only admin can call this entrypoint

Allows administrator to make any operation from the contract name (this can be useful to support another marketplaces that can arise in the future). Shortly: this entrypoint allows admin to run any code that does not change contract storage. There are examples of lambdas in the repository, one of which is [marketplace V3 swap](../contracts/lambdas/call/marketplaceV3Swap.ligo)

To compile lambda you can use docker version of LIGO compiler:
```console
docker run --rm -v "$PWD":"$PWD" -w "$PWD" ligolang/ligo:0.39.0 compile expression pascaligo lambda --init-file "contracts/lambdas/call/marketplaceV3Swap.ligo" > build/tz/lambdas/call/marketplace_v3_swap.tz
```

# Teia / h=n related entrypoints:
## mint\_OBJKT
- Expects `mintParams` that have the same interface that h=n `mint_OBJKT` entrypoint
- Expects no attached amount
- Emits mint operation to `mint_OBJKT` to the storage `minterAddress`
- Only admin can call this entrypoint

When this entrypoint is called all given params redirected to the h=n minter using split-contract name as a Source, so split-contract became creator of the minted objkt. This allows this contract receive and redistribute royalties in the future.

## swap
- Expects `swapParams` that have the same interface that h=n V2 marketplace `swap` entrypoint
- Expects no attached amount
- Emits mint operation to `swap` to the storage `marketplaceAddress`
- Only admin can call this entrypoint

The same as `mint_OBJKT` this `swap` call allows to swap token on V2 marketplace from the name of the collab contract. This entrypoint was not updated to V3 marketplace to keep backward compatibility. This is possible to swap using Teia V3 marketplace with lambda call.

## cancel\_swap
- Expects `cancelSwapParams` that have the same interface that h=n V2 marketplace `cancel_swap` entrypoint
- Expects no attached amount
- Emits mint operation to `cancel_swap` to the storage `marketplaceAddress`
- Only admin can call this entrypoint

This entrypoint allow to cancel swap from V2 marketplace.

## collect
- Expects `collectParams` that have the same interface that h=n V2 marketplace `collect` entrypoint
- Expects no attached amount
- Emits mint operation to `collect` to the storage `marketplaceAddress`
- Only admin can call this entrypoint

This entrypoint allows to collect other tokens from V2 marketplace.

## registry
- Expects `registryParams` that have the same interface that h=n registry `registry` entrypoint
- Expects no attached amount
- Emits mint operation to `registry` to the storage `registryAddress`
- Only admin can call this entrypoint

This entrypoint allows to change collab name / description in registry.

## unregistry
- Expects `unit` as parameter
- Expects no attached amount
- Emits mint operation to `unregistry` to the storage `registryAddress`
- Only admin can call this entrypoint

## update\_operators
- Expects FA2 `update_operators` as parameter
- Expects no attached amount
- Emits mint operation to `update_operators` to the storage `tokenAddress`
- Only admin can call this entrypoint

This entrypoint allows to make `update_operators` call from collab contract name which is required to interact from collab contract with another contracts (including marketplaces).

## transfer
- Expects FA2 `transfer` as parameter
- Expects no attached amount
- Emits mint operation to `transfer` to the storage `tokenAddress`
- Only admin can call this entrypoint

This entrypoint allows to make transfers from the collab contract name. It might be useful for airdrops.

# Management entrypoints:
## update\_admin
- Expects `address` of new administrator
- Expects no attached amount
- Changes storage `administrator` to new administrator
- Only admin can call this entrypoint

This can be useful to transfer admin rights to another address.

# Onchain views:
Onchain views is feature that was added in hangzhou protocol upgrade. This allows to make read-only synchronous calls to the contract to get some info onchain.
## get\_shares
- Expects `unit` as parameter
- Returns map with addresses as keys and shares as values for each participant from the contract

## get\_core\_participants
- Expects `unit` as parameter
- Returns set of participants that required to sign to be shown in UI

## get\_administrator
- Expects `unit` as parameter
- Returns administrator address

## get\_total\_received
- Expects `unit` as parameter
- Returns amount of xtz that was received by this collab during its existance time (might have interesting usecases I suppose)

## get\_total\_shares
- Expects `unit` as parameter
- Return amount of total shares in contract

# Errors:
- `MINT_NF`: error raised if minter is not properly configured during contract origination
- `SWAP_NF`: error raised if marketplace is not properly configured during contract origination
- `REG_NF`: error raised if registry is not properly configured during contract origination
- `ADDR_NF`: error raised if recipient address is not found
- `FA2_NF`: error raised if token is not properly configured during contract origination
- `AMNT_FRBD`: error raised if entrypoint is not expecting to receive any amount but gets some
- `NOT_ADM`: error raised if entrypoint is expected to be called by admin only and called by anyone else
- `WR_SHARES`: error raised during distribution if the sum of shares is not equal to total shares
- `WR_ADDR`: error raised if recipient address requested for withdraw have no splits in collab


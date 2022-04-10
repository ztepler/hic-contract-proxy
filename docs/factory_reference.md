# Factory
Factory allows admin to create set of templates that can be then used by anyone to originate any kind of contracts. Factory records any metadata after each contract creation. This can be used to keep tracking contract versions after template update. All this Factory mechanics is experiment that allow to create contracts that follow strictly defined properties (for example: admin can't change splits of the collab contract after it was created). Factory allows to have some `records` to be set to allow more variety in lambda execution (but this variety can be achieved by updating template lambdas).

# Factory entrypoints:
## create\_proxy
- Expects record with `templateName` which is `string` and `params` which is packed `bytes`
- Expects packed parameters 
- Expects no attached amount
- Originates collab contract using given template and parameters
- Adds originated contract address to the `originatedContracts` ledger with `metadata` returned from template execution
- Anyone can call this entrypoint

This entrypoint allows anyone to originate new collab contract using one of the templates provided by factory administrator. To create collab user should provide `templateName`, currently in mainnet only one template is supported which is `hic_collab` used to interact with h=n and Teia contracts. Calling this entrypoint runs template origination lambda that expecting some packed `params` to be executed. This params may vary for different templates. This params should be packed before passing to `create_proxy` entrypoint. See [MichelsonType.pack](https://pytezos.org/types.html) method to pack params using PyTezos. See [MichelCodePacker.packData](https://tezostaquito.io/typedoc/classes/_taquito_taquito.michelcodecpacker.html) method to pack params using taquito.

## add\_template
- Expects record with `name` which is `string` and `originateFunc` which is `(recordsType * bytes) -> originationResult`. And `originationResult` is record with origination `operation`, new contract `address` and `metadata` which is any `bytes` that will be written in `originatedContracts` ledger (it is easier to just read the code I suppose)
- Updates given template in `templates` ledger if it was existed under this `name` or adds new template if it wasn't
- Expects no attached amount
- Only admin can call this entrypoint

This entrypoint allows to add new templates to the Factory, as well as update existing templates.

## remove\_template
- Expects `string` with `name` of template that should be removed
- Removes template from `templates` ledger disallowing to create new contracts using this template
- Expects no attached amount
- Only admin can call this entrypoint

## add\_record
- Expects record with `name` which is `string` with name of added/updated record and `value` which is `bytes` value of this record
- Updates given record in `records` ledger if it was existed under this `name` or adds new record if it wasn't
- Expects no attached amount
- Only admin can call this entrypoint

This entrypoint allows to add/update record that can be used in templates.

## remove\_record
- Expects `string` with `name` of record that should be removed
- Removes record from `records` ledger
- Expects no attached amount
- Only admin can call this entrypoint

## update\_admin
- Expects `address` of proposed administrator
- Expects no attached amount
- Changes storage `proposedAdministrator` to proposed administrator
- Only admin can call this entrypoint

This entrypoint allows to transfer ownership. Proposed administrator should call `accept_ownership` to finish ownership transfer.

## accept\_ownership
- Expects `unit` as parameter
- Expects no attached amount
- Changes storage `administator` to proposed administrator
- Only proposed administrator can call this entrypoint

This entrypoint allows to finish ownership transfer.

## is\_originated\_contract
- Expects record with `contractAddress` which used to request and `callback` with type `contract(bool)`
- Emits transaction with `bool` answer whether this contract address was created by this Factory or it is not
- Expects no attached amount
- Anyone can call this entrypoint

This is callback view that can be used to request if given contract address was created by this factory.

# Errors
- `AMNT_FRBD`: error raised if entrypoint is not expecting to receive any amount but gets some
- `NOT_ADM`: error raised if entrypoint is expected to be called by admin only and called by anyone else
- `TEMPLATE_NF`: error raised if trying to `create_proxy` with template name that not existed
- `NOT_PROPOSED`: error raised if someone tries to `accept_ownership` but his address was not proposed
- `RECORD_NF`: error raised if template during execution tries to read record that not existed

### Hic origination lambda errors
- `UNPK_FAIL`: error raised if provided `params` can not be unpacked to be used in origination template
- `EXCEED_MAX_SHARES`: error raised if trying to create collab contract with more shares that it was tested for
- `EXCEED_MAX_PARTICIPANTS`: error raised if trying to create collab with too much participants


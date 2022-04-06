(* This is params that used in h=n mint call *)
type mintParams is record [
    address : address;
    amount : nat;
    metadata : bytes;
    royalties : nat
]


(* This is params that used in h=n marketplace swap call *)
type swapParams is michelson_pair(
    michelson_pair(address, "creator", nat, "objkt_amount"), "",
    michelson_pair(
        nat, "objkt_id",
        michelson_pair(nat, "royalties", tez, "xtz_per_objkt"),
        ""
    ), "")


(* This is params that used in h=n cancel_swap call *)
type cancelSwapParams is nat


(* This is params that used in h=n marketplace collect call *)
type collectParams is nat


(* This is params that used in h=n curate call *)
type curateParams is record [
    hDAO_amount : nat;
    objkt_id : nat
]


(* Params used in SUBJKT *)
type registryParams is record [
    metadata : bytes;
    subjkt : bytes;
]


(* TODO: the next methods look very similar. I tried to make an abstract call to hicetnunc
    method to reduce code repetition, but it became very complicated (because of the
    different params types in these calls). Maybe there are the way to simplify all this calls.
*)


(* This function used to make mint_OBJKT entrypoint operation *)
function callMintOBJKT(var minterAddress : address; var params : mintParams) : operation is
block {
    const hicReceiver : contract(mintParams) =
        case (Tezos.get_entrypoint_opt("%mint_OBJKT", minterAddress)
            : option(contract(mintParams))) of [
        | None -> (failwith("No minter found") : contract(mintParams))
        | Some(con) -> con
        ];

    const callToHic : operation = Tezos.transaction(params, 0tez, hicReceiver);
} with callToHic;


(* This function used to redirect swap call to hic et nunc swap entrypoint *)
function callSwap(var marketplaceAddress : address; var params : swapParams) : operation is
block {
    const hicReceiver : contract(swapParams) =
        case (Tezos.get_entrypoint_opt("%swap", marketplaceAddress)
            : option(contract(swapParams))) of [
        | None -> (failwith("No marketplace found") : contract(swapParams))
        | Some(con) -> con
        ];

    const callToHic : operation = Tezos.transaction(params, 0tez, hicReceiver);

} with callToHic;


(* This function used to redirect cancel swap call to hic et nunc cancel_swap entrypoint *)
function callCancelSwap(var marketplaceAddress : address; var params : cancelSwapParams) : operation is
block {
    const hicReceiver : contract(cancelSwapParams) =
        case (Tezos.get_entrypoint_opt("%cancel_swap", marketplaceAddress)
            : option(contract(cancelSwapParams))) of [
        | None -> (failwith("No marketplace found") : contract(cancelSwapParams))
        | Some(con) -> con
        ];

    const callToHic : operation = Tezos.transaction(params, 0tez, hicReceiver);

} with callToHic;


(* This function used to redirect collect call to hic et nunc collect entrypoint *)
function callCollect(var marketplaceAddress : address; var params : collectParams) : operation is
block {
    const hicReceiver : contract(collectParams) =
        case (Tezos.get_entrypoint_opt("%collect", marketplaceAddress)
            : option(contract(collectParams))) of [
        | None -> (failwith("No marketplace found") : contract(collectParams))
        | Some(con) -> con
        ];

    const callToHic : operation = Tezos.transaction(params, 0tez, hicReceiver);

} with callToHic;


(* This function used to redirect curate call to hic et nunc curate entrypoint *)
function callCurate(var minterAddress : address; var params : curateParams) : operation is
block {
    const hicReceiver : contract(curateParams) =
        case (Tezos.get_entrypoint_opt("%curate", minterAddress)
            : option(contract(curateParams))) of [
        | None -> (failwith("No minter found") : contract(curateParams))
        | Some(con) -> con
        ];

    const callToHic : operation = Tezos.transaction(params, 0tez, hicReceiver);

} with callToHic;


(* This function used to redirect registry call to hic et nunc registry entrypoint *)
function callRegistry(var registryAddress : address; var params : registryParams) : operation is
block {
    const receiver : contract(registryParams) =
        case (Tezos.get_entrypoint_opt("%registry", registryAddress)
            : option(contract(registryParams))) of [
        | None -> (failwith("No registry found") : contract(registryParams))
        | Some(con) -> con
        ];

    const callToHic : operation = Tezos.transaction(params, 0tez, receiver);

} with callToHic;


(* This function used to redirect unregistry call to hic et nunc registry entrypoint *)
function callUnregistry(var registryAddress : address) : operation is
block {
    const receiver : contract(unit) =
        case (Tezos.get_entrypoint_opt("%unregistry", registryAddress)
            : option(contract(unit))) of [
        | None -> (failwith("No registry found") : contract(unit))
        | Some(con) -> con
        ];

    const callToHic : operation = Tezos.transaction(Unit, 0tez, receiver);

} with callToHic;


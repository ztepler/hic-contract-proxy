(* This is params that used in h=n mint call *)
type mintParams is record [
    address : address;
    amount : nat;
    metadata : bytes;
    royalties : nat
]


(* This is params that used in h=n swap call *)
type swapParams is michelson_pair(
    nat, "objkt_amount",
    michelson_pair(nat, "objkt_id", tez, "xtz_per_objkt"),
"")


(* This is params that used in h=n cancel_swap call *)
type cancelSwapParams is nat


(* This is params that used in h=n collect call *)
type collectParams is record [
    objkt_amount : nat;
    swap_id : nat
]


(* This is params that used in h=n curate call *)
type curateParams is record [
    hDAO_amount : nat;
    objkt_id : nat
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
            : option(contract(mintParams))) of
        | None -> (failwith("No minter found") : contract(mintParams))
        | Some(con) -> con
        end;

    const callToHic : operation = Tezos.transaction(params, 0tez, hicReceiver);
} with callToHic;


(* This function used to redirect swap call to hic et nunc swap entrypoint *)
function callSwap(var minterAddress : address; var params : swapParams) : operation is
block {
    const hicReceiver : contract(swapParams) =
        case (Tezos.get_entrypoint_opt("%swap", minterAddress)
            : option(contract(swapParams))) of
        | None -> (failwith("No minter found") : contract(swapParams))
        | Some(con) -> con
        end;

    const callToHic : operation = Tezos.transaction(params, 0tez, hicReceiver);

} with callToHic;


(* This function used to redirect cancel swap call to hic et nunc cancel_swap entrypoint *)
function callCancelSwap(var minterAddress : address; var params : cancelSwapParams) : operation is
block {
    const hicReceiver : contract(cancelSwapParams) =
        case (Tezos.get_entrypoint_opt("%cancel_swap", minterAddress)
            : option(contract(cancelSwapParams))) of
        | None -> (failwith("No minter found") : contract(cancelSwapParams))
        | Some(con) -> con
        end;

    const callToHic : operation = Tezos.transaction(params, 0tez, hicReceiver);

} with callToHic;


(* This function used to redirect collect call to hic et nunc collect entrypoint *)
function callCollect(var minterAddress : address; var params : collectParams) : operation is
block {
    const hicReceiver : contract(collectParams) =
        case (Tezos.get_entrypoint_opt("%collect", minterAddress)
            : option(contract(collectParams))) of
        | None -> (failwith("No minter found") : contract(collectParams))
        | Some(con) -> con
        end;

    const callToHic : operation = Tezos.transaction(params, 0tez, hicReceiver);

} with callToHic;


(* This function used to redirect curate call to hic et nunc curate entrypoint *)
function callCurate(var minterAddress : address; var params : curateParams) : operation is
block {
    const hicReceiver : contract(curateParams) =
        case (Tezos.get_entrypoint_opt("%curate", minterAddress)
            : option(contract(curateParams))) of
        | None -> (failwith("No minter found") : contract(curateParams))
        | Some(con) -> con
        end;

    const callToHic : operation = Tezos.transaction(params, 0tez, hicReceiver);

} with callToHic;


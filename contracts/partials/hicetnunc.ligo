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


#include "../../main/HicProxy.ligo"

type callParams is record [
    marketplaceAddress : address;
    swap_id : nat;
]


function lambda(const _store : storage; const packedParams : bytes) : list(operation) is

block {

    const unpacked = case (Bytes.unpack(packedParams) : option(callParams)) of [
    | None -> (failwith("Unpack failed") : callParams)
    | Some(p) -> p
    ];

    const marketplace : contract(nat) =
        case (Tezos.get_entrypoint_opt("%cancel_swap", unpacked.marketplaceAddress)
            : option(contract(nat))) of [
        | None -> (failwith("Marketplace V3 is not found") : contract(nat))
        | Some(con) -> con
        ];

    const callToV3 : operation = Tezos.transaction(unpacked.swap_id, 0tez, marketplace);

} with list[callToV3]



#include "../../main/HicProxy.ligo"

type marketplaceV3Params is michelson_pair(
    address, "fa2",
    michelson_pair(
        nat, "objkt_id",
        michelson_pair(
            nat, "objkt_amount",
            michelson_pair(
                tez, "xtz_per_objkt",
                michelson_pair(
                    nat, "royalties",
                    address, "creator"
                ), ""
            ), ""
        ), ""
    ), ""
)

type callParams is record [
    marketplaceAddress : address;
    params : marketplaceV3Params;
]


function lambda(const _store : storage; const packedParams : bytes) : list(operation) is

block {

    const unpacked = case (Bytes.unpack(packedParams) : option(callParams)) of [
    | None -> (failwith("Unpack failed") : callParams)
    | Some(p) -> p
    ];

    const marketplace : contract(marketplaceV3Params) =
        case (Tezos.get_entrypoint_opt("%swap", unpacked.marketplaceAddress)
            : option(contract(marketplaceV3Params))) of [
        | None -> (failwith("Marketplace V3 is not found") : contract(marketplaceV3Params))
        | Some(con) -> con
        ];

    const callToV3 : operation = Tezos.transaction(unpacked.params, 0tez, marketplace);

} with list[callToV3]


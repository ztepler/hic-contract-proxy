#include "../../main/Factory.ligo"
#include "../../partials/hicetnunc.ligo"

(* TODO: in ideal this should be lambda function that stored in factory 
    under some name, currently this is function that emits mint

    there are should be multiple funcs with same interface
*)
function lambda(
    const factoryData : factoryData;
    const packedParams : bytes;
    const callSender : address) : executableCall is

block {

    const paramsOption: option(mintParams) = Bytes.unpack(packedParams);
    const params : mintParams = case paramsOption of
    | None -> (failwith("Unpack failed") : mintParams)
    | Some(p) -> p
    end;

    function callMint(const packedStore : bytes): list(operation) is
    block {
        (* TODO: unpack packedStore *)
        (* TODO: check that Tezos.sender is store.administrator *)
        checkSenderIsAdmin(store);

        (* Recording IPFS hash into store.mints: *)
        store.mints := Map.add (params.metadata, Unit, store.mints);

        const operations : list(operation) = nil;
        const callToHic = callMintOBJKT(store.hicetnuncMinterAddress, params);

        (*
        const hicReceiver : contract(mintParams) =
            case (Tezos.get_entrypoint_opt(
                "%mint_OBJKT",
                (store.hicetnuncMinterAddress : address)
                ) : option(contract(mintParams))) of
            | None -> (failwith("No minter found") : contract(mintParams))
            | Some(con) -> con
            end;

        const callToHic : operation = Tezos.transaction(params, 0tez, hicReceiver);
        *)

        (*TODO: pack store back? Looks too complicated. *)
    } with (operations, packedStore)
} with callMint

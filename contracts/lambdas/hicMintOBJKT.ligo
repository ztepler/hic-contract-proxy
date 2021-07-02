#include "../main/LambdaFactory.ligo"

(* TODO: in ideal this should be lambda function that stored in factory 
    under some name, currently this is function that emits mint

    there are should be multiple funcs with same interface
*)
function lambda(
    const factoryData : factoryData;
    const packedParams : customParams) : executableCall is

block {

    const paramsOption: option(mintParams) = Bytes.unpack(packedParams);
    const params : mintParams = case paramsOption of
    | None -> (failwith("Unpack failed") : mintParams)
    | Some(p) -> p
    end;

    function callMint(const p : unit): list(operation) is
    block {
        const operations : list(operation) = nil;
        const hicReceiver : contract(mintParams) =
            case (Tezos.get_entrypoint_opt(
                "%mint_OBJKT",
                (factoryData.hicetnuncMinterAddress : address)
                ) : option(contract(mintParams))) of
            | None -> (failwith("No minter found") : contract(mintParams))
            | Some(con) -> con
            end;

        const callToHic : operation = Tezos.transaction(params, 0tez, hicReceiver);

    } with operations
} with callMint

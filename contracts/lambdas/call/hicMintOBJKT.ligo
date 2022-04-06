#include "../../main/HicProxy.ligo"


function lambda(const store : storage; const packedParams : bytes) : list(operation) is

block {

    const paramsOption: option(mintParams) = Bytes.unpack(packedParams);
    const params : mintParams = case paramsOption of [
    | None -> (failwith("Unpack failed") : mintParams)
    | Some(p) -> p
    ];

    const callToHic = callMintOBJKT(store.minterAddress, params);

} with list[callToHic]

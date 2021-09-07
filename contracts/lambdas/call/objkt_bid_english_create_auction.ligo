#include "../../main/HicProxy.ligo"
#include "../../partials/objktBid.ligo"


function lambda(
    const store : storage;
    const packedParams : bytes) : list(operation) is

block {

    const paramsOption : option(placeEnglishParams) = Bytes.unpack(packedParams);
    const params : placeEnglishParams = case paramsOption of
    | None -> (failwith("Unpack failed") : placeEnglishParams)
    | Some(p) -> p
    end;

    const auctionAddress = params.auctionAddress;
    const auctionParams = params.auctionParams;

    const operator = record [
        owner = Tezos.self_address;
        operator = auctionAddress;
        // 1.0.0 is objkt_id:
        token_id = auctionParams.1.0.0;
    ];

    const addOperators = list[Add_operator(operator)];
    const removeOperators = list[Remove_operator(operator)];

    const allow = callUpdateOperators(store.tokenAddress, addOperators);
    const callToAuction = callPlaceEnglish(auctionAddress, auctionParams);
    const revoke = callUpdateOperators(store.tokenAddress, removeOperators);

} with list[allow; callToAuction; revoke]


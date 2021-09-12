(* Simple contract that can be used as a Gallery collab contract admin that
    allows anyone to swap thier item for a given price using Gallery collab.
    This contract is almost independent from Factory and Collabs but I decided
    that it would be easier to develop and experiment with it here.
*)


(* Including hic et nunc interface: *)
#include "../partials/hicetnunc.ligo"


(* Including common functions: *)
#include "../partials/general.ligo"


(* FA2 interface *)
#include "../partials/fa2.ligo"


type storage is record [
    galleryAddress : address;
    tokenAddress : address;
    marketplaceAddress : address;
    // TODO: swap owners to make possible to cancel swaps?
    // TODO: isPaused : bool;
    // TODO: administrator : address;
]

type action is
| Swap of swapParams
| Accept_gallery_ownership of unit
// TODO: | Trigger_pause of unit
// TODO: | Transfer_gallery_ownership of address OR Dismiss of unit
// TODO: | Cancel_swap of cancelSwapParams

(*
function checkIsNotPaused(var store : storage) : unit is
    if store.isPaused then failwith("Contract is paused")
    else unit;
*)

function swap(const store : storage; var params : swapParams) : (list(operation) * storage) is
block {
    checkNoAmount(Unit);
    // checkIsNotPaused(store);

    (* Transfering token from sender to the Gallery: *)
    const transferTokenParams = list[record [
        from_ = Tezos.sender;
        txs = list[ record [
            to_ = store.galleryAddress;
            // 1.0 is token_id:
            token_id = params.1.0;
            // 0.1 is amount:
            amount = params.0.1;
        ]];
    ]];
    const callTransferToken = callTransfer(store.tokenAddress, transferTokenParams);

    (* Allowing h=n Marketplace to spend token from the Gallery address
        - this call would be executed from Gallery using update_operators proxy
          entrypoint in the Gallery *)
    const operator = record [
        owner = store.galleryAddress;
        operator = store.marketplaceAddress;
        // 1.0 is token_id:
        token_id = params.1.0;
    ];
    const addOperators = list[Add_operator(operator)];
    const removeOperators = list[Remove_operator(operator)];

    (* Note that update operators calls goes to the gallery/proxy, not to the token itself: *)
    const allow = callUpdateOperators(store.galleryAddress, addOperators);
    const revoke = callUpdateOperators(store.galleryAddress, removeOperators);

    (* Calling swap *)
    const callToGallery = callSwap(store.galleryAddress, params);

    const operations = list[
        callTransferToken;
        allow;
        callToGallery;
        revoke
    ]

} with (operations, store)


function callAcceptOwnership(const galleryAddress : address) : operation is
block {
    const receiver : contract(unit) =
        case (Tezos.get_entrypoint_opt("%accept_ownership", galleryAddress)
            : option(contract(unit))) of
        | None -> (failwith("No gallery found") : contract(unit))
        | Some(con) -> con
        end;

    const acceptCall = Tezos.transaction(Unit, 0tez, receiver);
} with acceptCall


function acceptGalleryOwnership(const store : storage) : (list(operation) * storage) is
block {
    checkNoAmount(Unit);
    const acceptCall = callAcceptOwnership(store.galleryAddress);
} with (list[acceptCall], store)


function main (const params : action; const store : storage) : (list(operation) * storage) is
case params of
| Swap(p) -> swap(store, p)
| Accept_gallery_ownership -> acceptGalleryOwnership(store)
end

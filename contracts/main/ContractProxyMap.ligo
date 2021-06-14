(* Including hic et nunc interface: *)
#include "../partials/hicetnunc.ligo"


(* Including common functions: *)
#include "../partials/general.ligo"


type action is
| Mint_OBJKT of mintParams
| Swap of swapParams
| Cancel_swap of cancelSwapParams
| Collect of collectParams
| Curate of curateParams
| Default of unit
(* TODO: Views that would allow to make signatures in V2 *)


type storage is record [
    (* administrator is originator of the contract, this is the only one who can call mint *)
    administrator : address;
    (* TODO admins is a set too? *)

    (* shares is map of all participants with the shares that they would recieve *)
    shares : map(address, nat);

    (* the sum of the shares should be equal to totalShares *)
    totalShares : nat;

    (* address of the Hic Et Nunc Minter (mainnet: KT1Hkg5qeNhfwpKW4fXvq7HGZB9z2EnmCCA9) *)
    hicetnuncMinterAddress : address;

    (* set of participants that should sign and signs itself *)
    (* contract can call mint only when all core participant signed *)
    coreParticipants : set(address);
]


function checkSenderIsAdmin(var store : storage) : unit is
    if (Tezos.sender = store.administrator) then unit
    else failwith("Entrypoint can call only administrator");


function mint_OBJKT(var store : storage; const params: mintParams) : (list(operation) * storage) is
block {
    checkSenderIsAdmin(store);
    const callToHic = callMintOBJKT(store.hicetnuncMinterAddress, params);
} with (list[callToHic], store)


function swap(var store : storage; var params : swapParams) : (list(operation) * storage) is
block {
    checkSenderIsAdmin(store);
    const callToHic = callSwap(store.hicetnuncMinterAddress, params);
} with (list[callToHic], store)


function cancelSwap(var store : storage; var params : cancelSwapParams) : (list(operation) * storage) is
block {
    checkSenderIsAdmin(store);
    const callToHic = callCancelSwap(store.hicetnuncMinterAddress, params);
} with (list[callToHic], store)


function collect(var store : storage; var params : collectParams) : (list(operation) * storage) is
block {
    checkSenderIsAdmin(store);
    const callToHic = callCollect(store.hicetnuncMinterAddress, params);
} with (list[callToHic], store)


function curate(var store : storage; var params : curateParams) : (list(operation) * storage) is
block {
    checkSenderIsAdmin(store);
    const callToHic = callCurate(store.hicetnuncMinterAddress, params);
} with (list[callToHic], store)


function default(var store : storage) : (list(operation) * storage) is
block {
    var operations : list(operation) := nil;
    for participantAddress -> participantShare in map store.shares block {
        const payoutAmount : tez = Tezos.amount * participantShare / store.totalShares;

        const receiver : contract(unit) = getReceiver(participantAddress);
        const op : operation = Tezos.transaction(unit, payoutAmount, receiver);
        operations := op # operations
    }

    (* TODO: return dust to the last participant? *)
} with (operations, store)


function main (var params : action; var store : storage) : (list(operation) * storage) is
case params of
| Mint_OBJKT(p) -> mint_OBJKT(store, p)
| Swap(p) -> swap(store, p)
| Cancel_swap(p) -> cancelSwap(store, p)
| Collect(p) -> collect(store, p)
| Curate(p) -> curate(store, p)
| Default -> default(store)
end


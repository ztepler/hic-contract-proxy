(* Including hic et nunc interface: *)
#include "../partials/hicetnunc.ligo"


(* Including common functions: *)
#include "../partials/general.ligo"


type action is
| Mint_OBJKT of mintParams
| Swap of swapParams
| Default of unit


type storage is record [
    (* administrator is originator of the contract, this is the only one who can call mint *)
    administrator : address;

    (* shares is map of all participants with the shares that they would recieve *)
    shares : map(address, nat);

    (* address of the Hic Et Nunc Minter (mainnet: KT1Hkg5qeNhfwpKW4fXvq7HGZB9z2EnmCCA9) *)
    hicetnuncMinterAddress : address;
]


function checkSenderIsAdmin(var store : storage) : unit is
    if (Tezos.sender = store.administrator) then unit
    else failwith("Entrypoint can call only administrator");



function mint_OBJKT(var store : storage; var params : mintParams) : (list(operation) * storage) is
block {
    checkSenderIsAdmin(store);
    const callToHic = callMintOBJKT(store.hicetnuncMinterAddress, params);
} with (list[callToHic], store)


function swap(var store : storage; var params : swapParams) : (list(operation) * storage) is
block {
    checkSenderIsAdmin(store);
    const callToHic = callSwap(store.hicetnuncMinterAddress, params);
} with (list[callToHic], store)


function default(var store : storage) : (list(operation) * storage) is
block {
    var operations : list(operation) := nil;
    for participantAddress -> participantShare in map store.shares block {
        const payoutAmount : tez = Tezos.amount * participantShare / 1000n;

        const receiver : contract(unit) = getReceiver(participantAddress);
        const op : operation = Tezos.transaction(unit, payoutAmount, receiver);
        operations := op # operations
    }
} with (operations, store)


function main (var params : action; var store : storage) : (list(operation) * storage) is
case params of
| Mint_OBJKT(p) -> mint_OBJKT(store, p)
| Swap(p) -> swap(store, p)
| Default -> default(store)
end


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
| Is_participant_core of address
| Is_participant_administrator of address
| Get_total_shares of unit
| Get_participant_shares of address
| Is_minted_hash of bytes

(* TODO: Transfer method to withdraw tokens from contract *)
(* TODO: Transfer admin rights method? Can be very useful if someone needs
    transfer to DAO *)


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

    (* Bigmap with metadata of minted works, I decided not to use set because
        it is possible that collab would have unlimited works *)
    mints : big_map(bytes, unit);
]


function checkSenderIsAdmin(var store : storage) : unit is
    if (Tezos.sender = store.administrator) then unit
    else failwith("Entrypoint can call only administrator");


function mint_OBJKT(var store : storage; const params: mintParams) : (list(operation) * storage) is
block {
    checkSenderIsAdmin(store);

    (* Recording IPFS hash into store.mints: *)
    store.mints := Big_map.add (params.metadata, Unit, store.mints);
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


function tezToNat(const value : tez) : nat is value / 1mutez
function natToTez(const value : nat) : tez is value * 1mutez

(* natDiv required to prevent mutez overflow: *)
function natDiv(const value : tez; const num : nat; const den : nat) : tez is
    natToTez(tezToNat(value) * num / den)

function default(var store : storage) : (list(operation) * storage) is
block {
    var operations : list(operation) := nil;
    var opNumber : nat := 0n;
    var allocatedPayouts : tez := 0tez;

    for participantAddress -> participantShare in map store.shares block {
        opNumber := opNumber + 1n;
        const isLast : bool = opNumber = Set.size(store.shares);
        const payoutAmount : tez = if isLast
            then Tezos.amount - allocatedPayouts
            else natDiv(Tezos.amount, participantShare, store.totalShares);

        const receiver : contract(unit) = getReceiver(participantAddress);
        const op : operation = Tezos.transaction(unit, payoutAmount, receiver);

        if payoutAmount > 0tez then operations := op # operations else skip;
        allocatedPayouts := allocatedPayouts + payoutAmount;
    }

    (* TODO: return dust to the last participant? *)
} with (operations, store)


function isParticipantCore(var store : storage; var params : address) : (list(operation) * storage) is
block {
    skip;
} with ((nil: list(operation)), store)


function isParticipantAdministrator(var store : storage; var params : address) : (list(operation) * storage) is
block {
    skip;
} with ((nil: list(operation)), store)


function getTotalShares(var store : storage) : (list(operation) * storage) is
block {
    skip;
} with ((nil: list(operation)), store)


function getParticipantShares(var store : storage; var params : address) : (list(operation) * storage) is
block {
    skip;
} with ((nil: list(operation)), store)


function isMintedHash(var store : storage; var params : bytes) : (list(operation) * storage) is
block {
    skip;
} with ((nil: list(operation)), store)


function main (var params : action; var store : storage) : (list(operation) * storage) is
case params of
| Mint_OBJKT(p) -> mint_OBJKT(store, p)
| Swap(p) -> swap(store, p)
| Cancel_swap(p) -> cancelSwap(store, p)
| Collect(p) -> collect(store, p)
| Curate(p) -> curate(store, p)
| Default -> default(store)
| Is_participant_core(p) -> isParticipantCore(store, p)
| Is_participant_administrator(p) -> isParticipantAdministrator(store, p)
| Get_total_shares -> getTotalShares(store)
| Get_participant_shares(p) -> getParticipantShares(store, p)
| Is_minted_hash(p) -> isMintedHash(store, p)
end


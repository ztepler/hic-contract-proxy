#include "../partials/coreTypes.ligo"

(* Including hic et nunc interface: *)
#include "../partials/hicetnunc.ligo"


(* Including common functions: *)
#include "../partials/general.ligo"


(* Including sign interface *)
#include "../partials/sign.ligo"

(* TODO: import BasicProxy and its calls or move this calls into some core file? *)

type action is
| Execute of executableCall
| Default of unit
| Mint_OBJKT of mintParams
| Swap of swapParams
| Cancel_swap of cancelSwapParams
| Collect of collectParams
| Curate of curateParams
| Is_core_participant of isParticipantParams
| Is_participant_administrator of isParticipantParams
| Get_total_shares of getTotalSharesParams
| Get_participant_shares of getParticipantShares
| Is_minted_hash of isMintedHashParams

(* TODO: Transfer method to withdraw tokens from contract *)
(* TODO: Transfer admin rights method? Can be very useful if someone needs
    transfer to DAO *)
(* TODO: move some of the methods to BasicProxy? *)


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
    mints : map(bytes, unit);
    (* -- replacing big_map with map to test if this is the problem why contract
        creation is failing *)
]

function execute(const call : executableCall; const store : storage)
    : (list(operation) * storage) is

block {
    (* TODO: Check that Tezos.sender is factory *)
    const operations : list(operation) = call(Unit);
} with (operations, store)


function checkSenderIsAdmin(var store : storage) : unit is
    if (Tezos.sender = store.administrator) then unit
    else failwith("Entrypoint can call only administrator");


function mint_OBJKT(var store : storage; const params: mintParams) : (list(operation) * storage) is
block {
    checkSenderIsAdmin(store);

    (* Recording IPFS hash into store.mints: *)
    store.mints := Map.add (params.metadata, Unit, store.mints);
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


(* TODO: REPLACE THIS WITH ediv *)
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


function isCoreParticipant(var store : storage; var params : isParticipantParams) : (list(operation) * storage) is
block {
    const isCore = store.coreParticipants contains params.participantAddress;
    const returnOperation = Tezos.transaction(isCore, 0mutez, params.callback);
} with (list[returnOperation], store)


function isParticipantAdministrator(var store : storage; var params : isParticipantParams) : (list(operation) * storage) is
block {
    skip;
} with ((nil: list(operation)), store)


function getTotalShares(var store : storage; var params : getTotalSharesParams) : (list(operation) * storage) is
block {
    skip;
} with ((nil: list(operation)), store)


function getParticipantShares(var store : storage; var params : getParticipantShares) : (list(operation) * storage) is
block {
    skip;
} with ((nil: list(operation)), store)


function isMintedHash(var store : storage; var params : isMintedHashParams) : (list(operation) * storage) is
block {
    skip;
} with ((nil: list(operation)), store)


function main (const params : action; const store : storage) : (list(operation) * storage) is
case params of
| Execute(call) -> execute(call, store)
| Mint_OBJKT(p) -> mint_OBJKT(store, p)
| Swap(p) -> swap(store, p)
| Cancel_swap(p) -> cancelSwap(store, p)
| Collect(p) -> collect(store, p)
| Curate(p) -> curate(store, p)
| Default -> default(store)
| Is_core_participant(p) -> isCoreParticipant(store, p)
| Is_participant_administrator(p) -> isParticipantAdministrator(store, p)
| Get_total_shares(p) -> getTotalShares(store, p)
| Get_participant_shares(p) -> getParticipantShares(store, p)
| Is_minted_hash(p) -> isMintedHash(store, p)
end

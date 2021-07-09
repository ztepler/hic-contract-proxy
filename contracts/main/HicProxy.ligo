#include "../partials/coreTypes.ligo"

(* Including hic et nunc interface: *)
#include "../partials/hicetnunc.ligo"


(* Including common functions: *)
#include "../partials/general.ligo"


(* Including sign interface *)
#include "../partials/sign.ligo"

(* TODO: import BasicProxy and its calls or move this calls into some core file? *)


type storage is record [
    (* administrator is originator of the contract, this is the only one who can call mint *)
    administrator : address;
    (* TODO admins is a set too? *)

    proposedAdministrator : option(address);

    (* shares is map of all participants with the shares that they would recieve *)
    shares : map(address, nat);

    (* the sum of the shares should be equal to totalShares *)
    totalShares : nat;

    (* address of the Hic Et Nunc Minter (mainnet: KT1Hkg5qeNhfwpKW4fXvq7HGZB9z2EnmCCA9) *)
    minterAddress : address;

    (* address of the Hic Et Nunc marketplace *)
    marketplaceAddress : address;

    (* set of participants that should sign and signs itself *)
    (* contract can call mint only when all core participant signed *)
    coreParticipants : set(address);

    isPaused : bool;
]

type executableCall is storage -> list(operation)


type action is
| Execute of executableCall
| Default of unit
| Mint_OBJKT of mintParams
| Swap of swapParams
| Cancel_swap of cancelSwapParams
| Collect of collectParams
| Curate of curateParams
| Registry of registryParams
| Unregistry of unit
| Is_core_participant of isParticipantParams
| Is_participant_administrator of isParticipantParams
| Get_total_shares of getTotalSharesParams
| Get_participant_shares of getParticipantShares
| Update_manager of address
| Accept_ownership of unit
| Trigger_pause of unit

(* TODO: Transfer method to withdraw tokens from contract *)


function checkSenderIsAdmin(var store : storage) : unit is
    if (Tezos.sender = store.administrator) then unit
    else failwith("Entrypoint can call only administrator");


function execute(const call : executableCall; const store : storage)
    : (list(operation) * storage) is

block {
    (* TODO: check contract.isPaused is False *)
    checkSenderIsAdmin(store);
    const operations : list(operation) = call(store);
} with (operations, store)


function mint_OBJKT(var store : storage; const params: mintParams) : (list(operation) * storage) is
block {
    checkSenderIsAdmin(store);
    (* TODO: check if contract is paused or not *)

    const callToHic = callMintOBJKT(store.minterAddress, params);
} with (list[callToHic], store)


function swap(var store : storage; var params : swapParams) : (list(operation) * storage) is
block {
    checkSenderIsAdmin(store);
    const callToHic = callSwap(store.marketplaceAddress, params);
} with (list[callToHic], store)


function cancelSwap(var store : storage; var params : cancelSwapParams) : (list(operation) * storage) is
block {
    checkSenderIsAdmin(store);
    const callToHic = callCancelSwap(store.marketplaceAddress, params);
} with (list[callToHic], store)


function collect(var store : storage; var params : collectParams) : (list(operation) * storage) is
block {
    checkSenderIsAdmin(store);
    const callToHic = callCollect(store.marketplaceAddress, params);
} with (list[callToHic], store)


function curate(var store : storage; var params : curateParams) : (list(operation) * storage) is
block {
    checkSenderIsAdmin(store);
    const callToHic = callCurate(store.minterAddress, params);
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


function updateManager(var store : storage; var newManager : address) : (list(operation) * storage) is
block {
    (* TODO: record proposed manager to storage *)
    skip;
} with ((nil: list(operation)), store)


function acceptOwnership(var store : storage) : (list(operation) * storage) is
block {
    (* TODO: check that Tezos sender === proposed manager and change it *)
    skip;
} with ((nil: list(operation)), store)


function registry(var store : storage; var params : registryParams) : (list(operation) * storage) is
block {
    (* TODO: make call to h=n SUBJKT *)
    skip;
} with ((nil: list(operation)), store)


function unregistry(var store : storage) : (list(operation) * storage) is
block {
    (* TODO: make call to h=n SUBJKT *)
    skip;
} with ((nil: list(operation)), store)


function triggerPause(var store : storage) : (list(operation) * storage) is
block {
    (* TODO: set contract.isPaused to the opposite *)
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
| Update_manager(p) -> updateManager(store, p)
| Accept_ownership -> acceptOwnership(store)
| Registry(p) -> registry(store, p)
| Unregistry -> unregistry(store)
| Trigger_pause -> triggerPause(store)
end

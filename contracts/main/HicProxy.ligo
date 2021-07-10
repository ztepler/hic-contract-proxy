#include "../partials/factoryTypes.ligo"

(* Including hic et nunc interface: *)
#include "../partials/hicetnunc.ligo"


(* Including common functions: *)
#include "../partials/general.ligo"


(* Including sign interface *)
#include "../partials/sign.ligo"


(* FA2 interface *)
#include "../partials/fa2.ligo"

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

    (* hicetnunc fa2 token address *)
    tokenAddress : address;

    (* address of the Hic Et Nunc Minter (mainnet: KT1Hkg5qeNhfwpKW4fXvq7HGZB9z2EnmCCA9) *)
    minterAddress : address;

    (* address of the Hic Et Nunc marketplace *)
    marketplaceAddress : address;

    (* address of the Hic Et Nunc registry *)
    registryAddress : address;

    (* set of participants that should sign and signs itself *)
    (* contract can call mint only when all core participant signed *)
    coreParticipants : set(address);

    isPaused : bool;
]

type executableCall is storage*bytes -> list(operation)


type executeParams is record [
    lambda : executableCall;
    packedParams : bytes;
]


type action is
| Execute of executeParams
| Default of unit
| Mint_OBJKT of mintParams
| Swap of swapParams
| Cancel_swap of cancelSwapParams
| Collect of collectParams
| Curate of curateParams
| Registry of registryParams
| Unregistry of unit
| Update_operators of updateOperatorsParam
| Is_core_participant of isParticipantParams
| Is_administrator of isParticipantParams
| Get_total_shares of getTotalSharesParams
| Get_participant_shares of getParticipantShares
| Update_admin of address
| Accept_ownership of unit
| Trigger_pause of unit

(* TODO: Transfer method to withdraw tokens from contract *)


function checkSenderIsAdmin(var store : storage) : unit is
    if (Tezos.sender = store.administrator) then unit
    else failwith("Entrypoint can call only administrator");


function execute(const params : executeParams; const store : storage)
    : (list(operation) * storage) is

block {
    (* TODO: check contract.isPaused is False *)
    (* This is the only entrypoint (besides default) that allows tez in *)
    checkSenderIsAdmin(store);
    const operations : list(operation) =
        params.lambda(store, params.packedParams);
} with (operations, store)


function mint_OBJKT(var store : storage; const params: mintParams) : (list(operation) * storage) is
block {
    checkNoAmount(Unit);
    checkSenderIsAdmin(store);
    (* TODO: check if contract is paused or not *)

    const callToHic = callMintOBJKT(store.minterAddress, params);
} with (list[callToHic], store)


function swap(var store : storage; var params : swapParams) : (list(operation) * storage) is
block {
    checkNoAmount(Unit);
    checkSenderIsAdmin(store);
    const callToHic = callSwap(store.marketplaceAddress, params);
} with (list[callToHic], store)


function cancelSwap(var store : storage; var params : cancelSwapParams) : (list(operation) * storage) is
block {
    checkNoAmount(Unit);
    checkSenderIsAdmin(store);
    const callToHic = callCancelSwap(store.marketplaceAddress, params);
} with (list[callToHic], store)


function collect(var store : storage; var params : collectParams) : (list(operation) * storage) is
block {
    checkNoAmount(Unit);
    checkSenderIsAdmin(store);
    const callToHic = callCollect(store.marketplaceAddress, params);
} with (list[callToHic], store)


function curate(var store : storage; var params : curateParams) : (list(operation) * storage) is
block {
    checkNoAmount(Unit);
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
    checkNoAmount(Unit);

    const isCore = store.coreParticipants contains params.participantAddress;
    const returnOperation = Tezos.transaction(isCore, 0mutez, params.callback);
} with (list[returnOperation], store)


function isParticipantAdministrator(var store : storage; var params : isParticipantParams) : (list(operation) * storage) is
block {
    checkNoAmount(Unit);
    const isAdmin : bool = store.administrator = params.participantAddress;
    const returnOperation = Tezos.transaction(isAdmin, 0mutez, params.callback);
} with (list[returnOperation], store)


function getTotalShares(var store : storage; var callback : getTotalSharesParams) : (list(operation) * storage) is
block {
    checkNoAmount(Unit);
    const returnOperation = Tezos.transaction(store.totalShares, 0mutez, callback);
} with (list[returnOperation], store)


function getParticipantShares(var store : storage; var params : getParticipantShares) : (list(operation) * storage) is
block {
    checkNoAmount(Unit);
    const sharesCount : nat = case Map.find_opt(params.participantAddress, store.shares) of
    | Some(shares) -> shares
    | None -> 0n
    end;
    const returnOperation = Tezos.transaction(sharesCount, 0mutez, params.callback);
} with (list[returnOperation], store)


function updateAdmin(var store : storage; var newAdmin : address) : (list(operation) * storage) is
block {
    checkNoAmount(Unit);
    checkSenderIsAdmin(store);
    store.proposedAdministrator := Some(newAdmin);
} with ((nil: list(operation)), store)


function acceptOwnership(var store : storage) : (list(operation) * storage) is
block {
    checkNoAmount(Unit);

    const proposedAdministrator : address = case store.proposedAdministrator of
    | Some(proposed) -> proposed
    | None -> (failwith("Not proposed admin") : address)
    end;

    if Tezos.sender = proposedAdministrator then
    block {
        store.administrator := proposedAdministrator;
        store.proposedAdministrator := (None : option(address));
    } else failwith("Not proposed admin")

} with ((nil: list(operation)), store)


function registry(var store : storage; var params : registryParams) : (list(operation) * storage) is
block {
    checkNoAmount(Unit);
    checkSenderIsAdmin(store);
    const callToHic = callRegistry(store.registryAddress, params);
} with (list[callToHic], store)


function unregistry(var store : storage) : (list(operation) * storage) is
block {
    checkNoAmount(Unit);
    checkSenderIsAdmin(store);
    const callToHic = callUnregistry(store.registryAddress);
} with (list[callToHic], store)


function triggerPause(var store : storage) : (list(operation) * storage) is
block {
    (* TODO: set contract.isPaused to the opposite *)
    checkNoAmount(Unit);
    checkSenderIsAdmin(store);
    (* TODO: not implemented *)
} with ((nil: list(operation)), store)


function updateOperators(var store : storage; var params : updateOperatorsParam) : (list(operation) * storage) is
block {
    checkNoAmount(Unit);
    checkSenderIsAdmin(store);
    const callToHic = callUpdateOperators(store.tokenAddress, params);
} with (list[callToHic], store)


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
| Is_administrator(p) -> isParticipantAdministrator(store, p)
| Get_total_shares(p) -> getTotalShares(store, p)
| Get_participant_shares(p) -> getParticipantShares(store, p)
| Update_admin(p) -> updateAdmin(store, p)
| Accept_ownership -> acceptOwnership(store)
| Registry(p) -> registry(store, p)
| Unregistry -> unregistry(store)
| Trigger_pause -> triggerPause(store)
| Update_operators(p) -> updateOperators(store, p)
end

(* Including hic et nunc interface: *)
#include "../partials/hicetnunc.ligo"


(* Including common functions: *)
#include "../partials/general.ligo"


(* Including sign interface *)
#include "../partials/sign.ligo"


(* FA2 interface *)
#include "../partials/fa2.ligo"

(*
- administrator is originator of the contract, this is the only one who can call mint
- shares is map of all participants with the shares that they would recieve
- totalShares is the sum of the shares should be equal to totalShares
- tokenAddress is hicetnunc fa2 token address
- miterAddress is address of the Hic Et Nunc Minter
- marketplaceAddress address of the Hic Et Nunc V2 marketplace
- registryAddress is address of the Hic Et Nunc registry
- coreParticipants set of participants that should sign and signs itself
- isPaused is flag that can be triggered by admin that turns off mint/swap entries
- totalReceived - is amount of mutez that was received by a collab
- threshold - is minimal amount that can be payed to the participant during default split
- undistributed - is mapping with all undistributed values
- residuals - is amount of mutez that wasn't distributed and kept until next income
*)

type storage is record [
    administrator : address;
    shares : map(address, nat);
    totalShares : nat;
    tokenAddress : address;
    minterAddress : address;
    marketplaceAddress : address;
    registryAddress : address;
    coreParticipants : set(address);
    isPaused : bool;
    totalReceived : nat;
    threshold : nat;
    undistributed : map(address, nat);
    residuals : nat;
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
| Registry of registryParams
| Unregistry of unit
| Update_operators of updateOperatorsParam
| Update_admin of address
| Transfer of transferParams
| Set_threshold of nat
| Withdraw of address


function checkSenderIsAdmin(var store : storage) : unit is
    if (Tezos.sender = store.administrator) then unit
    else failwith("Entrypoint can call only administrator");


function execute(const params : executeParams; const store : storage)
    : (list(operation) * storage) is

block {
    (* This is the only entrypoint (besides default) that allows tez in *)
    checkSenderIsAdmin(store);
    const operations : list(operation) =
        params.lambda(store, params.packedParams);
} with (operations, store)


function mint_OBJKT(var store : storage; const params: mintParams) : (list(operation) * storage) is
block {
    checkNoAmount(Unit);
    checkSenderIsAdmin(store);
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


[@inline] function getUndistributed(const participant : address; const store : storage) is
    case Map.find_opt(participant, store.undistributed) of [
    | Some(value) -> value
    | None -> 0n
    ]


function default(var store : storage) : (list(operation) * storage) is
block {
    var operations : list(operation) := nil;
    var allocatedPayouts := 0n;
    const natAmount = tezToNat(Tezos.amount);
    const distAmount = natAmount + store.residuals;
    store.totalReceived := store.totalReceived + natAmount;

    for participantAddress -> participantShare in map store.shares block {
        var payoutAmount := distAmount * participantShare / store.totalShares;
        allocatedPayouts := allocatedPayouts + payoutAmount;

        payoutAmount := payoutAmount + getUndistributed(participantAddress, store);

        if payoutAmount >= store.threshold
        then store.undistributed[participantAddress] := 0n
        else block {
            store.undistributed[participantAddress] := payoutAmount;
            payoutAmount := 0n;
        };

        const receiver : contract(unit) = getReceiver(participantAddress);
        const payout : tez = natToTez(payoutAmount);
        const op : operation = Tezos.transaction(unit, payout, receiver);

        if payout > 0tez then operations := op # operations else skip;
    };

    const residuals = distAmount - allocatedPayouts;
    if residuals >= 0
    then store.residuals := abs(residuals)
    else failwith("Wrong share configuration")

} with (operations, store)


function updateAdmin(var store : storage; var newAdmin : address) : (list(operation) * storage) is
block {
    checkNoAmount(Unit);
    checkSenderIsAdmin(store);
    store.administrator := newAdmin;
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


function updateOperators(var store : storage; var params : updateOperatorsParam) : (list(operation) * storage) is
block {
    checkNoAmount(Unit);
    checkSenderIsAdmin(store);
    const callToHic = callUpdateOperators(store.tokenAddress, params);
} with (list[callToHic], store)


function transfer(var store : storage; var params : transferParams) : (list(operation) * storage) is
block {
    checkNoAmount(Unit);
    checkSenderIsAdmin(store);
    const callToHic = callTransfer(store.tokenAddress, params);
} with (list[callToHic], store)


function set_threshold(const store : storage; const newThreshold : nat) is
block {
    checkNoAmount(Unit);
    checkSenderIsAdmin(store);
} with ((nil: list(operation)), store with record [threshold = newThreshold])


function withdraw(var store : storage; var recipient : address) is
block {
    (* anyone can trigger withdraw for anyone *)
    checkNoAmount(Unit);
    const receiver = getReceiver(recipient);
    const payout = natToTez(getUndistributed(recipient, store));
    store.undistributed[recipient] := 0n;
    const op = Tezos.transaction(unit, payout, receiver);
} with (list[op], store)


function main (const params : action; const store : storage) : (list(operation) * storage) is
case params of [
| Execute(call) -> execute(call, store)
| Mint_OBJKT(p) -> mint_OBJKT(store, p)
| Swap(p) -> swap(store, p)
| Cancel_swap(p) -> cancelSwap(store, p)
| Collect(p) -> collect(store, p)
| Default -> default(store)
| Update_admin(p) -> updateAdmin(store, p)
| Registry(p) -> registry(store, p)
| Unregistry -> unregistry(store)
| Update_operators(p) -> updateOperators(store, p)
| Transfer(p) -> transfer(store, p)
| Set_threshold(p) -> set_threshold(store, p)
| Withdraw(p) -> withdraw(store, p)
]

[@view] function get_shares (const _ : unit ; const s : storage) is s.shares
[@view] function get_core_participants (const _ : unit; const s : storage) is s.coreParticipants
[@view] function get_administrator (const _ : unit; const s : storage) is s.administrator
[@view] function get_total_received (const _ : unit; const s : storage) is s.totalReceived
[@view] function get_total_shares (const _ : unit; const s : storage) is s.totalShares


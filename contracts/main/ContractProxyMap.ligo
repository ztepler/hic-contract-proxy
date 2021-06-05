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
| Sign of mintParams
| FinalizeMint of unit


(* Ledger with flags is core participant signed or not *)
type signsLedger is map(address, bool)


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

    (* suggested mint that should be signed by all core participants to proceed *)
    suggestedMint : option(mintParams);

    (* set of participants that should sign and signs itself *)
    (* contract can call mint only when all core participant signed *)
    coreParticipants : set(address);
    signs : set(address);
]


function checkSenderIsAdmin(var store : storage) : unit is
    if (Tezos.sender = store.administrator) then unit
    else failwith("Entrypoint can call only administrator");


(* Mint does not call real minting, it is just create suggestion.
    The name keeped to make easier integration with frontend *)
function mint_OBJKT(var store : storage; const params: mintParams) : (list(operation) * storage) is
block {

    checkSenderIsAdmin(store);
    store.signs := (set [] : set(address));
    store.suggestedMint := Some(params);

} with ((nil: list(operation)), store)


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


function checkAllCoreSigned(const core : set(address); const signs : set(address)) : unit is
block {
    var isAllSigned : bool := True;
    (* TODO: try to remove brackets *)
    for participant in set core block {
        isAllSigned := signs contains participant and isAllSigned
    };

    if isAllSigned then skip else failwith("Can't mint while proposal is not signed");
} with unit


function getSuggestedMintOrFail(const suggestedMint : option(mintParams)) : mintParams is
    case suggestedMint of
    | Some(mint) -> mint
    | None -> (failwith("No mint is proposed") : mintParams)    
    end;


function finalizeMint(var store : storage) : (list(operation) * storage) is
block {

    checkAllCoreSigned(store.coreParticipants, store.signs);
    const suggestedMint : mintParams = getSuggestedMintOrFail(store.suggestedMint);
    const callToHic = callMintOBJKT(store.hicetnuncMinterAddress, suggestedMint);

    store.signs := (set [] : set(address));
    store.suggestedMint := (None : option(mintParams));

} with (list[callToHic], store)


function sign(var store : storage; const signParams : mintParams) : (list(operation) * storage) is
block {

    const suggestedMint : mintParams = getSuggestedMintOrFail(store.suggestedMint);

    (* Checking that participant signs suggested params and they are not changed: *)
    if signParams =/= suggestedMint
    then failwith("Signing params differ from suggested")
    else skip;

    if store.coreParticipants contains Tezos.sender then skip
    else failwith("Sender is not core participant");

    store.signs := Set.add (Tezos.sender, store.signs);

} with ((nil: list(operation)), store)


function main (var params : action; var store : storage) : (list(operation) * storage) is
case params of
| Mint_OBJKT(p) -> mint_OBJKT(store, p)
| Swap(p) -> swap(store, p)
| Cancel_swap(p) -> cancelSwap(store, p)
| Collect(p) -> collect(store, p)
| Curate(p) -> curate(store, p)
| Default -> default(store)
| Sign(p) -> sign(store, p)
| FinalizeMint -> finalizeMint(store)
end


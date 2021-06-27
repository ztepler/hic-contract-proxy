(* Including sign interface *)
#include "../partials/sign.ligo"


type signParams is record [
    (* Address of the contratract that used to mint OBJKT *)
    collabContract: address;

    (* IPFS hash of minted work: *)
    metadata: bytes;
]

type isSignedResponse is bool

type isSignedParams is record [
    participant: address;
    metadata: bytes;
    callback: contract(isSignedResponse)
]

type action is
| Sign of signParams
| Is_signed of isSignedParams
| Is_core_participant_callback of bool
| Is_minted_hash_callback of bool


type storage is record [
    signatures: big_map(address*bytes, unit);

    (* Address of the collab contract that queried about participant/minted hash: *)
    callContract: option(address);

    (* Queried params: isCoreParticipant and isMintedHash *)
    isCoreParticipant: option(bool);
    // isMintedHash: option(bool);
]


function sign(var store : storage; var params : signParams) : (list(operation) * storage) is
block {
    (* TODO: allow to create signatures for pre-V1 contracts?
        (for those contract that have no views?) *)
    store.callContract := Some(params.collabContract);

    (* Creating two operations:
        1. Callback that collab have Tezos.sender as core participant: *)
    const isCoreEntrypointOption = (
        Tezos.get_entrypoint_opt("%is_core_participant", params.collabContract)
            : option(contract(isParticipantParams)));

    const isCoreEntrypoint : contract(isParticipantParams) = case isCoreEntrypointOption of
        | Some(con) -> con
        | None -> (failwith("Collab have no core participant view") : contract(isParticipantParams))
        end;

    const isCoreCall = record [
        participantAddress = Tezos.sender;
        callback = (Tezos.self("%is_core_participant_callback") : contract(bool));
    ];

    (* 2. Callback that collab have minted IPFS hash *)
    const isMintedEntrypointOption = (
        Tezos.get_entrypoint_opt("%is_minted_hash", params.collabContract)
            : option(contract(isMintedHashParams)));

    const isMintedEntrypoint : contract(isMintedHashParams) = case isMintedEntrypointOption of
        | Some(con) -> con
        | None -> (failwith("Collab have no minted hash view") : contract(isMintedHashParams))
        end;

    const isMintedCall = record [
        metadata = params.metadata;
        callback = (Tezos.self("%is_minted_hash_callback") : contract(bool));
    ];

    const operations : list(operation) = list [
        Tezos.transaction(isCoreCall, 0mutez, isCoreEntrypoint);
        Tezos.transaction(isMintedCall, 0mutez, isMintedEntrypoint);
    ];

} with (operations, store)


function isCoreParticipantCallback(var store : storage; var isCoreParticipant : bool) is
block {
    (* 1. Check that this is expected answer from collab contract that was called *)
    (* 2. Record isCoreParticipant *)
    skip;
} with ((nil: list(operation)), store)


function isMintedHashCallback(var store : storage; var isMintedHash : bool) is
block {
    (* 1. Check that this is expected answer from collab contract that was called *)
    (* 2. Check that isCoreParticipant True *)
    (* 3. Finish signing process and add new record to store.signatures *)

    (* Clearing callContract: *)
    store.callContract := (None : option(address));
    skip;
} with ((nil: list(operation)), store)


function isSigned(var store : storage; var params : isSignedParams) : (list(operation) * storage) is
block {
    (* Return is participant*metadata within store.signatures *)
    skip;
} with ((nil: list(operation)), store)


function main (var params : action; var store : storage) : (list(operation) * storage) is
case params of
| Sign(p) -> sign(store, p)
| Is_signed(p) -> isSigned(store, p)
| Is_core_participant_callback(p) -> isCoreParticipantCallback(store, p)
| Is_minted_hash_callback(p) -> isMintedHashCallback(store, p)
end

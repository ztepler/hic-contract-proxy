#include "../../main/LambdaFactory.ligo"
#include "../../main/BasicProxy.ligo"


type participantRec is record [
    (* share is the fraction that participant would receive from every sale *)
    share : nat;

    (* role isCore allow participant to sign as one of the creator *)
    isCore : bool;
]

type participantsMap is map(address, participantRec);

(*  I was unable to make contract using Tezos.create_contract.
    I don't undertand what happened in next few lines.
    I just copypasted and adapted next code from QuipuSwap factory:
*)
type createProxyFuncType is (option(key_hash) * tez * storage) -> (operation * address)

const createProxyFunc : createProxyFuncType =
[%Michelson ( {| { UNPPAIIR ;
                  CREATE_CONTRACT
#include "../../../build/tz/basic_proxy.tz"
        ;
          PAIR } |}
 : createProxyFuncType)];


function lambda(
    const data : factoryData;
    const packedParams : bytes) : operation is

block {

    const participantsOption: option(participantsMap) = Bytes.unpack(packedParams);
    const participants : participantsMap = case participantsOption of
    | None -> (failwith("Unpack failed") : participantsMap)
    | Some(p) -> p
    end;

    (* Calculating total shares and core participants: *)
    var shares : map(address, nat) := map [];
    var coreParticipants : set (address) := set [];
    var totalShares : nat := 0n;
    var coreCount : nat := 0n;

    for participantAddress -> participantRec in map participants block {
        shares[participantAddress] := participantRec.share;
        totalShares := totalShares + participantRec.share;

        if participantRec.isCore then
        block {
            coreParticipants := Set.add (participantAddress, coreParticipants);
            coreCount := coreCount + 1n;
        } else skip;
    };

    if totalShares = 0n then failwith("Sum of the shares should be more than 0n")
    else skip;

    if coreCount = 0n then failwith("Collab contract should have at least one core")
    else skip;

    (* TODO: check how much participants it can handle and limit this count here *)

    (* Preparing initial storage: *)
    (* TODO: decide where this params should be:
        a) in proxy-contract
        b) in factory
        c) for some contracts in factory (for that who returns id to redistribute)
            and for some in proxy-contract
    *)
    (* TODO: move this to factory storage (if decided b or c)
    const initialStore : storage = record[
        administrator = Tezos.sender;
        shares = shares;
        totalShares = totalShares;
        hicetnuncMinterAddress = factoryStore.hicetnuncMinterAddress;
        coreParticipants = coreParticipants;
        mints = (big_map [] : big_map(bytes, unit));
    ];
    *)
    const initialStore : storage = record [
        id = data.originatedContracts;
        factory = Tezos.self_address;
    ];

    (* Making originate operation: *)
    const origination : operation * address = createProxyFunc (
        (None : option(key_hash)),
        0tz,
        initialStore);

} with origination.0

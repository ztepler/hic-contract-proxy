#include "../../main/Factory.ligo"
#include "../../main/HicProxy.ligo"


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
#include "../../../build/tz/hic_proxy.tz"
        ;
          PAIR } |}
 : createProxyFuncType)];


function lambda(
    const data : factoryData;
    const packedParams : bytes) : originationResult is

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

    const initialStore : storage = record [
        administrator = Tezos.sender;
        proposedAdministrator = (None : option(address));
        shares = shares;
        totalShares = totalShares;
        minterAddress = data.minterAddress;
        marketplaceAddress = data.marketplaceAddress;
        tokenAddress = data.tokenAddress;
        coreParticipants = coreParticipants;
        isPaused = False;
    ];

    (* Making originate operation: *)
    const origination : operation * address = createProxyFunc (
        (None : option(key_hash)),
        0tz,
        initialStore);

    const result : originationResult = record [
        operation = origination.0;
        address = origination.1;
        metadata = Bytes.pack("hic_proxy");
    ];

} with result

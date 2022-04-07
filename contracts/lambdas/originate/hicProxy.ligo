#include "../../partials/factory.ligo"
#include "../../main/HicProxy.ligo"
#include "../../partials/proxyTypes.ligo"


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
    const records : recordsType;
    const packedParams : bytes) : originationResult is

block {

    const participantsOption: option(participantsMap) = Bytes.unpack(packedParams);
    const participants : participantsMap = case participantsOption of [
    | None -> (failwith("Unpack failed") : participantsMap)
    | Some(p) -> p
    ];

    (* Calculating total shares and core participants: *)
    var shares : map(address, nat) := map [];
    var undistributed : map(address, nat) := map [];
    var coreParticipants : set (address) := set [];
    var totalShares : nat := 0n;

    for participantAddress -> participantRec in map participants block {
        shares[participantAddress] := participantRec.share;
        undistributed[participantAddress] := 0n;
        totalShares := totalShares + participantRec.share;

        if participantRec.isCore
        then coreParticipants := Set.add (participantAddress, coreParticipants)
        else skip;
    };

    if totalShares = 0n then failwith("Sum of the shares should be more than 0n")
    else skip;

    if totalShares > 1_000_000_000_000n then
        failwith("The maximum shares is 10**12")
    else skip;

    if Map.size(participants) > 108n then failwith("The maximum participants count is 108")
    else skip;

    (* Preparing initial storage: *)
    const initialStore : storage = record [
        administrator = Tezos.sender;
        proposedAdministrator = (None : option(address));
        shares = shares;
        totalShares = totalShares;
        minterAddress = unpackAddressRecord("hicMinterAddress", records);
        marketplaceAddress = unpackAddressRecord("hicMarketplaceAddress", records);
        tokenAddress = unpackAddressRecord("hicTokenAddress", records);
        registryAddress = unpackAddressRecord("hicRegistryAddress", records);
        coreParticipants = coreParticipants;
        isPaused = False;
        totalReceived = 0n;
        threshold = 0n;
        undistributed = undistributed;
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

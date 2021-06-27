#include "ContractProxyMap.ligo"


type createProxyFuncType is (option(key_hash) * tez * storage) -> (operation * address)


(* I did not find the way to create contract using Tezos.create_contract, so
    I adapted and copypasted code with createProxyFunc from QuipuSwap factory:
*)
const createProxyFunc : createProxyFuncType =
[%Michelson ( {| { UNPPAIIR ;
                  CREATE_CONTRACT
#include "../../build/tz/contract_proxy_map.tz"
        ;
          PAIR } |}
 : createProxyFuncType)];


type factoryStorage is record [
    originatedContracts : nat;
    hicetnuncMinterAddress : address;
]

type participantRec is record [
    (* share is the fraction that participant would receive from every sale *)
    share : nat;

    (* role isCore allow participant to sign as one of the creator *)
    isCore : bool;
]

(* map of all participants with their shares and roles *)
type originationParams is map(address, participantRec);


type factoryAction is
| Create_proxy of originationParams


function createProxy(const participants : originationParams; var factoryStore : factoryStorage)
    : (list(operation) * factoryStorage) is
block {

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
    const initialStore : storage = record[
        administrator = Tezos.sender;
        shares = shares;
        totalShares = totalShares;
        hicetnuncMinterAddress = factoryStore.hicetnuncMinterAddress;
        coreParticipants = coreParticipants;
        mints = (big_map [] : big_map(bytes, unit));
    ];

    (* Making originate operation: *)
    const origination : operation * address = createProxyFunc (
        (None : option(key_hash)),
        0tz,
        initialStore);
    factoryStore.originatedContracts := factoryStore.originatedContracts + 1n;

} with (list[origination.0], factoryStore)


function main (const params : factoryAction; var factoryStore : factoryStorage)
    : (list(operation) * factoryStorage) is
case params of
| Create_proxy(p) -> createProxy(p, factoryStore)
end

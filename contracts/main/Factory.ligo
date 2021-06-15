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


type originationParams is record [
    (* administrator is originator of the contract, this is the only one who can call mint *)
    administrator : address;

    (* shares is map of all participants with the shares that they would recieve *)
    shares : map(address, nat);

    (* set of participants that should sign before contract can mint *)
    coreParticipants : set(address);
]


type factoryAction is
| Create_proxy of originationParams


function createProxy(const params : originationParams; var factoryStore : factoryStorage)
    : (list(operation) * factoryStorage) is
block {

    (* Calculating total shares: *)
    var totalShares : nat := 0n;
    for participantAddress -> participantShare in map params.shares block {
        totalShares := totalShares + participantShare;
    };

    if totalShares = 0n then failwith("Sum of the shares should be more than 0n")
    else skip;

    (* TODO: check how much participants it can handle and limit this count here *)

    (* Preparing initial storage: *)
    const initialStore : storage = record[
        administrator = params.administrator;
        shares = params.shares;
        totalShares = totalShares;
        hicetnuncMinterAddress = factoryStore.hicetnuncMinterAddress;
        coreParticipants = params.coreParticipants;
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

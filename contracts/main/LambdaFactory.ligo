#include "LambdaProxy.ligo"


type createProxyFuncType is (option(key_hash) * tez * storage) -> (operation * address)


(* I did not find the way to create contract using Tezos.create_contract, so
    I adapted and copypasted code with createProxyFunc from QuipuSwap factory:
*)
const createProxyFunc : createProxyFuncType =
[%Michelson ( {| { UNPPAIIR ;
                  CREATE_CONTRACT
#include "../../build/tz/lambda_proxy.tz"
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

type executeParams is record [
    params : customParams;
    proxy : address;
    lambdaName : string;
]

type factoryAction is
| Create_proxy of originationParams
| Execute_proxy of executeParams
(* TODO: add_lambda function method that saves lambda to storage *)
(* TODO: Execute type can be record of params (bytes) + saved lambda name *)
(*      and lambda need to know how to unpack bytes *)
(* TODO: income entrypoint that would accept redirected defaults from collabs *)

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
    (* TODO: move this to factory storage
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
        id = 0n;
        factory = Tezos.self_address;
    ];

    (* Making originate operation: *)
    const origination : operation * address = createProxyFunc (
        (None : option(key_hash)),
        0tz,
        initialStore);
    factoryStore.originatedContracts := factoryStore.originatedContracts + 1n;

} with (list[origination.0], factoryStore)


(* TODO: in ideal this should be lambda function that stored in factory 
    under some name, currently this is function that emits mint

    there are should be multiple funcs with same interface
*)
function callEmitter(
    const factoryStore : factoryStorage;
    const packedParams : customParams) : executableCall is

block {

    const paramsOption: option(mintParams) = Bytes.unpack(packedParams);
    const params : mintParams = case paramsOption of
    | None -> (failwith("Unpack failed") : mintParams)
    | Some(p) -> p
    end;

    function callMint(const p : unit): list(operation) is
    block {
        const operations : list(operation) = nil;
        const hicReceiver : contract(mintParams) =
            case (Tezos.get_entrypoint_opt(
                "%mint_OBJKT",
                (factoryStore.hicetnuncMinterAddress : address)
                ) : option(contract(mintParams))) of
            | None -> (failwith("No minter found") : contract(mintParams))
            | Some(con) -> con
            end;

        const callToHic : operation = Tezos.transaction(params, 0tez, hicReceiver);

    } with operations
} with callMint


(* TODO: LambdaProxy call method *)
function executeProxy(var params : executeParams; var factoryStore : factoryStorage) : (list(operation) * factoryStorage) is
block {
    const call : executableCall = callEmitter(factoryStore, params.params);

    const receiver : contract(executableCall) =
        case (Tezos.get_entrypoint_opt("%execute", params.proxy)
            : option(contract(executableCall))) of
        | None -> (failwith("No proxy found") : contract(executableCall))
        | Some(con) -> con
        end;

    const op : operation = Tezos.transaction(call, 0tez, receiver);

} with (list[op], factoryStore)

(* TODO: default method *)

function main (const params : factoryAction; var factoryStore : factoryStorage)
    : (list(operation) * factoryStorage) is
case params of
| Create_proxy(p) -> createProxy(p, factoryStore)
| Execute_proxy(p) -> executeProxy(p, factoryStore)
end

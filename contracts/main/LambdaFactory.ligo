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


type factoryData is record [
    originatedContracts : nat;
    hicetnuncMinterAddress : address;
]


type createCallType is (factoryData * customParams) -> executableCall


type factoryStorage is record [
    data : factoryData;

    (* Collection of callable lambdas that could be added to contract: *)
    lambdas : map(string, createCallType);
]

(* TODO: different contracts means that they can have different constructors,
    so maybe it is good to convert this constuctor params in bytes too and
    construction method in lambda too :)
*)
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

type addLambdaParams is record [
    name : string;
    lambda : createCallType;
]

type factoryAction is
| Create_proxy of originationParams
| Execute_proxy of executeParams
| Add_lambda of addLambdaParams
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
        id = factoryStore.data.originatedContracts;
        factory = Tezos.self_address;
    ];

    (* Making originate operation: *)
    const origination : operation * address = createProxyFunc (
        (None : option(key_hash)),
        0tz,
        initialStore);
    factoryStore.data.originatedContracts := factoryStore.data.originatedContracts + 1n;

} with (list[origination.0], factoryStore)


function executeProxy(
    const params : executeParams;
    const factoryStore : factoryStorage) : (list(operation) * factoryStorage) is

block {
    (* TODO: think about all this names *)
    const optionalEmitter = Map.find_opt(params.lambdaName, factoryStore.lambdas);
    const callEmitter : createCallType = case optionalEmitter of
    | Some(emitter) -> emitter
    | None -> (failwith("Lambda is not found") : createCallType)
    end;
    const call : executableCall = callEmitter(factoryStore.data, params.params);

    (* TODO: load executableCall from storage *)
    (* TODO: should it check that params.proxy created by this factory? *)
    const receiver : contract(executableCall) =
        case (Tezos.get_entrypoint_opt("%execute", params.proxy)
            : option(contract(executableCall))) of
        | None -> (failwith("No proxy found") : contract(executableCall))
        | Some(con) -> con
        end;

    const op : operation = Tezos.transaction(call, 0tez, receiver);

} with (list[op], factoryStore)


function add_lambda(
    const params : addLambdaParams;
    var factoryStore : factoryStorage) : (list(operation) * factoryStorage) is

block {
    (* TODO: should it check that this name is not existed or rewrite is good? *)
    factoryStore.lambdas[params.name] := params.lambda;
} with ((nil : list(operation)), factoryStore)

(* TODO: default method from contract that receives values? 
    - or it is not required now?
    - maybe it is good to support contracts that does not distribute by itself, but
        returns all xtz to the factory and then run there some logic (maybe with
        bigmap distributions)
*)
(* TODO: method to add new executableCall *)

function main (const params : factoryAction; var factoryStore : factoryStorage)
    : (list(operation) * factoryStorage) is
case params of
| Create_proxy(p) -> createProxy(p, factoryStore)
| Execute_proxy(p) -> executeProxy(p, factoryStore)
| Add_lambda(p) -> add_lambda(p, factoryStore)
end

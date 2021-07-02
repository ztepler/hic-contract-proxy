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


type participantRec is record [
    (* share is the fraction that participant would receive from every sale *)
    share : nat;

    (* role isCore allow participant to sign as one of the creator *)
    isCore : bool;
]
(* TODO: different contracts means that they can have different constructors,
    so maybe it is good to convert this constuctor params in bytes too and
    construction method in lambda too :)
*)
type participantsMap is map(address, participantRec);


type createCallType is (factoryData * customParams) -> executableCall
type originateContractType is (factoryData * participantsMap) -> (list(operation) * factoryData)


type factoryStorage is record [
    data : factoryData;

    (* Collection of callable lambdas that could be added to contract: *)
    lambdas : map(string, createCallType);
    contracts : map(string, originateContractType);
]


(* map of all participants with their shares and roles *)
type originationParams is record [
    contractName : string;

    (* TODO: convert participants to bytes? *)
    participants : participantsMap;
]

type executeParams is record [
    params : customParams;
    proxy : address;
    lambdaName : string;
]

type addLambdaParams is record [
    name : string;
    lambda : createCallType;
]

type addContractParams is record [
    name : string;
    contract : originateContractType;
]

type factoryAction is
| Create_proxy of originationParams
| Execute_proxy of executeParams
| Add_lambda of addLambdaParams
| Add_contract of addContractParams
(* TODO: add_lambda function method that saves lambda to storage *)
(* TODO: Execute type can be record of params (bytes) + saved lambda name *)
(*      and lambda need to know how to unpack bytes *)
(* TODO: income entrypoint that would accept redirected defaults from collabs *)

function createProxy(const params : originationParams; var factoryStore : factoryStorage)
    : (list(operation) * factoryStorage) is
block {

    (* TODO: think about all this names too *)
    const optionalOriginator = Map.find_opt(params.contractName, factoryStore.contracts);
    const proxyOriginator : originateContractType = case optionalOriginator of
    | Some(originator) -> originator
    | None -> (failwith("Contract is not found") : originateContractType)
    end;

    const operationAndData = proxyOriginator(factoryStore.data, params.participants);
    (* TODO: the next code is hard to understand, maybe need to change the type
        what proxyOriginator returned?
        for example: one origination operation?
            and move change data to this func? *)
    const originatieOperations = operationAndData.0;
    factoryStore.data := operationAndData.1;

} with (originatieOperations, factoryStore)


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
    (* TODO: check that called by factory admin *)
    (* TODO: should it check that this name is not existed or rewrite is good? *)
    factoryStore.lambdas[params.name] := params.lambda;
} with ((nil : list(operation)), factoryStore)


function add_contract(
    const params : addContractParams;
    var factoryStore : factoryStorage) : (list(operation) * factoryStorage) is

block {
    (* TODO: check that called by factory admin *)
    (* TODO: should it check that this name is not existed or rewrite is good? *)
    factoryStore.contracts[params.name] := params.contract;
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
| Add_contract(p) -> add_contract(p, factoryStore)
end

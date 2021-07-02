#include "../partials/coreTypes.ligo"

type factoryData is record [
    (* TODO: move this minter address to specific origination of hic proxy *)
    hicetnuncMinterAddress : address;

    (* TODO: temporal solution to make this factoryData record *)
    anotherRecord : string;
]

(* TODO: should this types be merged into one?
    - they are very similar in type, but different in logic *)
type createCallType is (factoryData * bytes) -> executableCall
type originateContractType is (factoryData * bytes) -> originationResult


type factoryStorage is record [
    data : factoryData;

    (* Collection of callable lambdas that could be added to contract: *)
    lambdas : map(string, createCallType);
    contracts : map(string, originateContractType);

    (* Ledger with all originated contracts and their params *)
    originatedContracts : big_map(address, bytes);
]


type originationParams is record [
    contractName : string;
    params : bytes;
    (* TODO: add context with some data, in example h=n minter address? *)
]

type executeParams is record [
    lambdaName : string;
    params : bytes;
    proxy : address;
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

    const result : originationResult = proxyOriginator(
        factoryStore.data, params.params);

    factoryStore.originatedContracts[result.address] := result.metadata;

} with (list[result.operation], factoryStore)


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

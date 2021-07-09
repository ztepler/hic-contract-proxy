#include "../partials/coreTypes.ligo"

type factoryData is record [
    (* TODO: move this minter address to specific origination of hic proxy *)
    minterAddress : address;
    marketplaceAddress : address;
    registryAddress : address;
]

type originateContractType is (factoryData * bytes) -> originationResult


type factoryStorage is record [
    data : factoryData;

    contracts : map(string, originateContractType);

    (* Ledger with all originated contracts and their params *)
    originatedContracts : big_map(address, bytes);
]


type originationParams is record [
    contractName : string;
    params : bytes;
    (* TODO: add context with some data, in example h=n minter address? *)
]


type addContractParams is record [
    name : string;
    contract : originateContractType;
]

type factoryAction is
| Create_proxy of originationParams
| Add_contract of addContractParams
| Is_originated_contract of address


function createProxy(const params : originationParams; var factoryStore : factoryStorage)
    : (list(operation) * factoryStorage) is
block {

    (* TODO: check if factory is paused or not *)
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


function addContract(
    const params : addContractParams;
    var factoryStore : factoryStorage) : (list(operation) * factoryStorage) is

block {
    (* TODO: check that called by factory admin *)
    (* TODO: should it check that this name is not existed or rewrite is good? *)
    factoryStore.contracts[params.name] := params.contract;
} with ((nil : list(operation)), factoryStore)


function isOriginatedContract(
    const contractAddress : address;
    var factoryStore : factoryStorage) is

block {
    (* TODO: implement this view *)
    skip;
} with ((nil : list(operation)), factoryStore)


function main (const params : factoryAction; var factoryStore : factoryStorage)
    : (list(operation) * factoryStorage) is
case params of
| Create_proxy(p) -> createProxy(p, factoryStore)
| Add_contract(p) -> addContract(p, factoryStore)
| Is_originated_contract(p) -> isOriginatedContract(p, factoryStore)
end

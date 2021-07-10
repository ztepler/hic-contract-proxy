#include "../partials/coreTypes.ligo"

(* TODO: need to decide: is it better to have all this data inside factory or
    it is better to have them inside bytes that transfered when contract originated? *)
type factoryData is record [
    minterAddress : address;
    marketplaceAddress : address;
    registryAddress : address;
    tokenAddress : address;
]

type originateContractFunc is (factoryData * bytes) -> originationResult


type factoryStorage is record [
    data : factoryData;

    templates : map(string, originateContractFunc);

    (* Ledger with all originated contracts and their params *)
    originatedContracts : big_map(address, bytes);
]


type originationParams is record [
    templateName : string;
    params : bytes;
    (* TODO: add context with some data, in example h=n minter address? *)
]


type addTemplateParams is record [
    name : string;
    originateFunc : originateContractFunc;
]

type factoryAction is
| Create_proxy of originationParams
| Add_template of addTemplateParams
| Remove_template of string
| Is_originated_contract of address


function createProxy(const params : originationParams; var factoryStore : factoryStorage)
    : (list(operation) * factoryStorage) is
block {

    (* TODO: think about all this names too *)
    const optionalOriginator = Map.find_opt(params.templateName, factoryStore.templates);
    const proxyOriginator : originateContractFunc = case optionalOriginator of
    | Some(originator) -> originator
    | None -> (failwith("Template is not found") : originateContractFunc)
    end;

    const result : originationResult = proxyOriginator(
        factoryStore.data, params.params);

    factoryStore.originatedContracts[result.address] := result.metadata;

} with (list[result.operation], factoryStore)


function addTemplate(
    const params : addTemplateParams;
    var factoryStore : factoryStorage) : (list(operation) * factoryStorage) is

block {
    (* TODO: check that called by factory admin *)
    (* Rewriting contract with the same name is allowed: *)
    factoryStore.templates[params.name] := params.originateFunc;
} with ((nil : list(operation)), factoryStore)


function removeTemplate(
    const templateName : string;
    var factoryStore : factoryStorage) : (list(operation) * factoryStorage) is

block {
    (* TODO: check that called by factory admin *)
    factoryStore.templates := Big_map.remove(templateName, factoryStore.templates);
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
| Add_template(p) -> addTemplate(p, factoryStore)
| Remove_template(p) -> removeTemplate(p, factoryStore)
| Is_originated_contract(p) -> isOriginatedContract(p, factoryStore)
end

#include "../partials/factory.ligo"
#include "../partials/general.ligo"


type factoryAction is
| Create_proxy of originationParams
| Add_template of addTemplateParams
| Remove_template of string
| Is_originated_contract of isOriginatedParams
| Update_admin of address
| Accept_ownership of unit
| Add_record of addRecordParams
| Remove_record of string


function checkSenderIsAdmin(const factoryStore : factoryStorage) : unit is
    if (Tezos.sender = factoryStore.administrator) then unit
    else failwith("Entrypoint can call only administrator");


function createProxy(const params : originationParams; var factoryStore : factoryStorage)
    : (list(operation) * factoryStorage) is
block {

    checkNoAmount(Unit);
    const optionalOriginator = Map.find_opt(params.templateName, factoryStore.templates);
    const proxyOriginator : originateContractFunc = case optionalOriginator of [
    | Some(originator) -> originator
    | None -> (failwith("Template is not found") : originateContractFunc)
    ];

    const result : originationResult = proxyOriginator(
        factoryStore.records, params.params);

    factoryStore.originatedContracts[result.address] := result.metadata;

} with (list[result.operation], factoryStore)


function addTemplate(
    const params : addTemplateParams;
    var factoryStore : factoryStorage) : (list(operation) * factoryStorage) is

block {
    checkNoAmount(Unit);
    checkSenderIsAdmin(factoryStore);
    (* Rewriting contract with the same name is allowed: *)
    factoryStore.templates[params.name] := params.originateFunc;
} with ((nil : list(operation)), factoryStore)


function removeTemplate(
    const templateName : string;
    var factoryStore : factoryStorage) : (list(operation) * factoryStorage) is

block {
    checkNoAmount(Unit);
    checkSenderIsAdmin(factoryStore);
    factoryStore.templates := Big_map.remove(templateName, factoryStore.templates);
} with ((nil : list(operation)), factoryStore)



function isOriginatedContract(
    const params : isOriginatedParams;
    var factoryStore : factoryStorage) is

block {
    checkNoAmount(Unit);
    const isOriginatedOption = Big_map.find_opt(params.contractAddress, factoryStore.originatedContracts);
    const isOriginated : bool = case isOriginatedOption of [
    | Some(_metadata) -> True
    | None -> False
    ];

    const returnOperation = Tezos.transaction(isOriginated, 0mutez, params.callback);
} with (list[returnOperation], factoryStore)


function updateAdmin(var factoryStore : factoryStorage; const newAdmin : address) : (list(operation) * factoryStorage) is
block {
    checkNoAmount(Unit);
    checkSenderIsAdmin(factoryStore);
    factoryStore.proposedAdministrator := Some(newAdmin);
} with ((nil: list(operation)), factoryStore)


function acceptOwnership(var factoryStore : factoryStorage) : (list(operation) * factoryStorage) is
block {
    checkNoAmount(Unit);

    const proposedAdministrator : address = case factoryStore.proposedAdministrator of [
    | Some(proposed) -> proposed
    | None -> (failwith("Not proposed admin") : address)
    ];

    if Tezos.sender = proposedAdministrator then
    block {
        factoryStore.administrator := proposedAdministrator;
        factoryStore.proposedAdministrator := (None : option(address));
    } else failwith("Not proposed admin")

} with ((nil: list(operation)), factoryStore)


function addRecord(
    const params : addRecordParams;
    var factoryStore : factoryStorage) : (list(operation) * factoryStorage) is

block {
    checkNoAmount(Unit);
    checkSenderIsAdmin(factoryStore);
    (* Rewriting record with the same name is allowed: *)
    factoryStore.records[params.name] := params.value;
} with ((nil : list(operation)), factoryStore)


function removeRecord(
    const name : string;
    var factoryStore : factoryStorage) : (list(operation) * factoryStorage) is

block {
    checkNoAmount(Unit);
    checkSenderIsAdmin(factoryStore);
    factoryStore.records := Big_map.remove(name, factoryStore.records);
} with ((nil : list(operation)), factoryStore)


function main (const params : factoryAction; var factoryStore : factoryStorage)
    : (list(operation) * factoryStorage) is
case params of [
| Create_proxy(p) -> createProxy(p, factoryStore)
| Add_template(p) -> addTemplate(p, factoryStore)
| Remove_template(p) -> removeTemplate(p, factoryStore)
| Is_originated_contract(p) -> isOriginatedContract(p, factoryStore)
| Update_admin(p) -> updateAdmin(factoryStore, p)
| Accept_ownership -> acceptOwnership(factoryStore)
| Add_record(p) -> addRecord(p, factoryStore)
| Remove_record(p) -> removeRecord(p, factoryStore)
]

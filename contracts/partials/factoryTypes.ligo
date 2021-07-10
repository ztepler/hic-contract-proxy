type originationResult is record [
    operation : operation;
    address : address;
    metadata : bytes;
]


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

    administrator : address;
    proposedAdministrator : option(address);
]


type originationParams is record [
    templateName : string;
    params : bytes;
]


type addTemplateParams is record [
    name : string;
    originateFunc : originateContractFunc;
]


type isOriginatedResponse is bool


type isOriginatedParams is record [
    contractAddress: address;
    callback: contract(isOriginatedResponse)
]

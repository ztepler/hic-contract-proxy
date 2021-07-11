type originationResult is record [
    operation : operation;
    address : address;
    metadata : bytes;
]


type recordsType is big_map(string, bytes)


type originateContractFunc is (recordsType * bytes) -> originationResult


type factoryStorage is record [
    (* Records is packed factory params that can be accessed in originate
        lambdas, so it can be used to store contract-specific data: *)
    records : recordsType;

    (* Templates is map of lambdas each of one should originate contract *)
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


type addRecordParams is record [
    name : string;
    value : bytes;
]

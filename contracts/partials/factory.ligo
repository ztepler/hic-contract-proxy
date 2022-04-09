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


function unpackAddressRecord(
    const name : string;
    const records : recordsType
) : address is
block {

    (* Getting record by its name: *)
    const packedRecord : bytes = case Big_map.find_opt(name, records) of [
    | None -> (failwith("RECORD_NF") : bytes)
    | Some(rec) -> rec
    ];

    (* Unpacking record to address type: *)
    const addressOption: option(address) = Bytes.unpack(packedRecord);
    const unpackedAddress : address = case addressOption of [
    | None -> (failwith("UNPK_FAIL") : address)
    | Some(adr) -> adr
    ];

} with unpackedAddress

type signParams is record [
    (* Address of the contratract that used to mint OBJKT *)
    collabContract: address;

    (* IPFS hash of minted work: *)
    metadata: bytes;
]

type isSignedParams is record [
    participant: address;
    metadata: bytes;
]

type isSignedResponse is bool

type action is
| Sign of signParams
| Is_signed of isSignedParams


type storage is record [
    signatures: big_map(address*bytes, unit);
]


function sign(var store : storage; var params : signParams) : (list(operation) * storage) is
block {
    (* TODO: allow to create signatures for pre-V1 contracts?
        (for those contract that have no views?) *)
    (* 1. Check if collab have Tezos.sender *)
    (* 2. Check if collab have minted IPFS hash *)
    (* 3. Add new record to store.signatures *)
    skip;
} with ((nil: list(operation)), store)


function isSigned(var store : storage; var params : isSignedParams) : (list(operation) * storage) is
block {
    (* Return is participant*metadata within store.signatures *)
    skip;
} with ((nil: list(operation)), store)


function main (var params : action; var store : storage) : (list(operation) * storage) is
case params of
| Sign(p) -> sign(store, p)
| Is_signed(p) -> isSigned(store, p)
end

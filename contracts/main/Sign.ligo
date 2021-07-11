type isSignedResponse is bool

type isSignedParams is record [
    participant: address;
    id: nat;
    callback: contract(isSignedResponse)
]


type action is
| Sign of nat
| Unsign of nat
| Is_signed of isSignedParams
(* TODO: maybe add method for oracle that can confirm that this OBJKT
    is really made by this participant? *)

type signKey is (address*nat)

type storage is record [
    signatures: big_map(signKey, unit);
]


function sign(var store : storage; const signId : nat) : (list(operation) * storage) is
block {
    const key : signKey = (Tezos.sender, signId);
    store.signatures[key] := Unit;
} with ((nil: list(operation)), store)


function unsign(var store : storage; const signId : nat) : (list(operation) * storage) is
block {
    const key : signKey = (Tezos.sender, signId);
    store.signatures := Big_map.remove(key, store.signatures);
} with ((nil: list(operation)), store)


function isSigned(var store : storage; var params : isSignedParams) : (list(operation) * storage) is
block {
    const key : signKey = (params.participant, params.id);
    const isSigned : bool = case Big_map.find_opt(key, store.signatures) of
    | Some(u) -> True
    | None -> False
    end;
    const returnOperation = Tezos.transaction(isSigned, 0mutez, params.callback);
} with (list[returnOperation], store)


function main (var params : action; var store : storage) : (list(operation) * storage) is
case params of
| Sign(p) -> sign(store, p)
| Unsign(p) -> unsign(store, p)
| Is_signed(p) -> isSigned(store, p)
end

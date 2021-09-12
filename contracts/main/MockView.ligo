type storage is record [
    natValue : option(nat);
    boolValue : option(bool);
]

type action is
| Nat_view of nat
| Bool_view of bool

function dispatchAction(const param : action) : storage is
case param of
| Nat_view(p) -> record [
    natValue = Some(p);
    boolValue = (None : option(bool))
]

| Bool_view(p) -> record [
    natValue = (None : option(nat));
    boolValue = Some(p)
]
end

function main(const param : action; const _store : storage)
    : (list(operation) * storage) is
        ((nil: list(operation)), dispatchAction(param))

#include "../partials/coreTypes.ligo"


type shares is map(address, nat);


type storage is record [
    factory : address;
    administrator : address;
    totalShares : nat;
    shares : shares;
]

type executableCall is storage -> list(operation)


type action is
| Execute of executableCall
| Default of unit


function default(const store : storage) : (list(operation) * storage) is
block {
    var operations : list(operation) := nil;
    (* Just simple operation to the factory with nat contract ID or without *)
} with (operations, store)


function checkSenderIsAdmin(var store : storage) : unit is
    if (Tezos.sender = store.administrator) then unit
    else failwith("Entrypoint can call only administrator");


function execute(const call : executableCall; const store : storage)
    : (list(operation) * storage) is

block {
    checkSenderIsAdmin(store);
    const operations : list(operation) = call(store);
} with (operations, store)


function main (const params : action; const store : storage) : (list(operation) * storage) is
case params of
| Execute(call) -> execute(call, store)
| Default -> default(store)
end

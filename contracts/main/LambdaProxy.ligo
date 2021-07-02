#include "../partials/hicetnunc.ligo"

type executableCall is unit -> list(operation)


type action is
| Execute of executableCall
| Default of unit

type storage is record [
    id : nat;
    factory : address;
]

function default(const store : storage) : (list(operation) * storage) is
block {
    var operations : list(operation) := nil;
    (* Just simple operation to the factory with nat contract ID or without *)
} with (operations, store)


function execute(const call : executableCall; const store : storage)
    : (list(operation) * storage) is

block {
    (* TODO: Check that Tezos.sender is factory *)
    const operations : list(operation) = call(Unit);
} with (operations, store)


function main (const params : action; const store : storage) : (list(operation) * storage) is
case params of
| Execute(call) -> execute(call, store)
| Default -> default(store)
end

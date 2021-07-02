#include "../partials/coreTypes.ligo"
(* TODO: import BasicProxy and its calls or move this calls into some core file? *)

type action is
| Execute of executableCall
| Default of unit

type storage is record [
    (* administrator is originator of the contract, this is the only one who can call mint *)
    administrator : address;
    (* TODO admins is a set too? *)

    (* shares is map of all participants with the shares that they would recieve *)
    shares : map(address, nat);

    (* the sum of the shares should be equal to totalShares *)
    totalShares : nat;

    (* address of the Hic Et Nunc Minter (mainnet: KT1Hkg5qeNhfwpKW4fXvq7HGZB9z2EnmCCA9) *)
    hicetnuncMinterAddress : address;

    (* set of participants that should sign and signs itself *)
    (* contract can call mint only when all core participant signed *)
    coreParticipants : set(address);

    (* Bigmap with metadata of minted works, I decided not to use set because
        it is possible that collab would have unlimited works *)
    mints : big_map(bytes, unit);
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

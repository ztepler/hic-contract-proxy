#include "../../partials/factory.ligo"
#include "../../main/BasicProxy.ligo"


(*  I was unable to make contract using Tezos.create_contract.
    I don't undertand what happened in next few lines.
    I just copypasted and adapted next code from QuipuSwap factory:
*)
type createProxyFuncType is (option(key_hash) * tez * storage) -> (operation * address)

const createProxyFunc : createProxyFuncType =
[%Michelson ( {| { UNPPAIIR ;
                  CREATE_CONTRACT
#include "../../../build/tz/basic_proxy.tz"
        ;
          PAIR } |}
 : createProxyFuncType)];


function lambda(
    const _records : recordsType;
    const packedParams : bytes) : originationResult is

block {

    const shares : shares = case (Bytes.unpack(packedParams) : option(shares)) of
    | None -> (failwith("Unpack failed") : shares)
    | Some(p) -> p
    end;

    (* Calculating total shares and core participants: *)
    var totalShares : nat := 0n;

    for _participantAddress -> share in map shares block {
        totalShares := totalShares + share;
    };

    if totalShares = 0n then failwith("Sum of the shares should be more than 0n")
    else skip;

    (* TODO: check how much participants it can handle and limit this count here *)
    (* Preparing initial storage: *)

    const initialStore : storage = record [
        factory = Tezos.self_address;
        administrator = Tezos.sender;
        totalShares = totalShares;
        shares = shares;
    ];

    (* Making originate operation: *)
    const origination : operation * address = createProxyFunc (
        (None : option(key_hash)),
        0tz,
        initialStore);

    const result : originationResult = record [
        operation = origination.0;
        address = origination.1;
        metadata = Bytes.pack("basic_proxy")
    ];

} with result

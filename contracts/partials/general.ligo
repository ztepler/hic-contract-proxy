function getReceiver(var a : address) : contract(unit) is
    case (Tezos.get_contract_opt(a): option(contract(unit))) of [
    | Some (con) -> con
    | None -> (failwith ("ADDR_NF") : (contract(unit)))
    ];


function checkAllCoreSigned(const core : set(address); const signs : set(address)) : unit is
block {
    var isAllSigned : bool := True;
    for participant in set core block {
        isAllSigned := signs contains participant and isAllSigned
    };

    if isAllSigned then skip else failwith("NOT_SIGNED");
} with unit


function tezToNat(const value : tez) : nat is value / 1mutez
function natToTez(const value : nat) : tez is value * 1mutez


function checkNoAmount(const _p : unit) : unit is
    if (Tezos.amount = 0tez) then unit
    else failwith("AMNT_FRBD");


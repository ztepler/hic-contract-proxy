function getReceiver(var a : address) : contract(unit) is
    case (Tezos.get_contract_opt(a): option(contract(unit))) of
    | Some (con) -> con
    | None -> (failwith ("Not a contract") : (contract(unit)))
    end;


function checkAllCoreSigned(const core : set(address); const signs : set(address)) : unit is
block {
    var isAllSigned : bool := True;
    for participant in set core block {
        isAllSigned := signs contains participant and isAllSigned
    };

    if isAllSigned then skip else failwith("Can't mint while proposal is not signed");
} with unit


function tezToNat(const value : tez) : nat is value / 1mutez
function natToTez(const value : nat) : tez is value * 1mutez


function checkNoAmount(const p : unit) : unit is
    if (Tezos.amount = 0tez) then unit
    else failwith("This entrypoint should not receive tez");

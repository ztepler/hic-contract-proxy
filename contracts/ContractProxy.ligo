(* This is params that used in h=n mint call *)
type mintParams is record [
    address : address;
    amount : nat;
    metadata : bytes;
    royalties : nat
]


type action is
| Mint of mintParams
| Withdraw of unit


type storage is record [
    (* administrator is originator of the contract, this is the only one who can call mint *)
    administrator : address;

    (* share value would be nat that in sum should be equal to 1000 *)
    shares : map(address, nat);

    (* balances is earned values that was  *)
    balances : map(address, tez);

    (* account value after last revenue distribution, used to calculate how much value
        NOTE: it is implied that it is not possible to move tez from contract in any way
        other than using withdraw call
    *)
    lastDistributedValue : tez;

    (* is token minted or not *)
    isMinted : bool;

    (* address of the Hic Et Nunc Minter (mainnet: KT1Hkg5qeNhfwpKW4fXvq7HGZB9z2EnmCCA9) *)
    hicetnuncMinterAddress : address;
]


function mint(var s : storage; var p : mintParams) : (list(operation) * storage) is
block {
    const hicReceiver : contract(mintParams) =
        case (Tezos.get_entrypoint_opt("%mint_OBJKT", s.hicetnuncMinterAddress) : option(contract(mintParams))) of
        | None -> (failwith("No minter found") : contract(mintParams))
        | Some(con) -> con
        end;

    const callToHic : operation = Tezos.transaction(p, 0tez, hicReceiver);
} with (list[callToHic], s)


function getReceiver(var a : address) : contract(unit) is
    case (Tezos.get_contract_opt(a): option(contract(unit))) of
    | Some (con) -> con
    | None -> (failwith ("Not a contract") : (contract(unit)))
    end;


function withdraw(var s : storage) : (list(operation) * storage) is
block {
    const receiver : contract(unit) = getReceiver(Tezos.sender);
    const payoutAmount : tez = 0tez;
    const payoutOperation : operation = Tezos.transaction(unit, payoutAmount, receiver);
} with (list[payoutOperation], s)


function main (var params : action; var s : storage) : (list(operation) * storage) is
case params of
| Mint(p) -> mint(s, p)
| Withdraw -> withdraw(s)
end

(* This is params that used in h=n mint call *)
type mintParams is record [
    address : address;
    amount : nat;
    metadata : bytes;
    royalties : nat
]


(* This is params that used in h=n swap call *)
type swapParams is michelson_pair(
    nat, "objkt_amount",
    michelson_pair(nat, "objkt_id", tez, "xtz_per_objkt"),
"")


type action is
| Mint_OBJKT of mintParams
| Swap of swapParams
| Default of unit


type storage is record [
    (* administrator is originator of the contract, this is the only one who can call mint *)
    administrator : address;

    (* shares is map of all participants with the shares that they would recieve *)
    shares : map(address, nat);

    (* address of the Hic Et Nunc Minter (mainnet: KT1Hkg5qeNhfwpKW4fXvq7HGZB9z2EnmCCA9) *)
    hicetnuncMinterAddress : address;
]


function mint(var s : storage; var p : mintParams) : (list(operation) * storage) is
block {
    if (Tezos.sender = s.administrator) then skip
    else failwith("Entrypoint mint can call only administrator");

    const hicReceiver : contract(mintParams) =
        case (Tezos.get_entrypoint_opt("%mint_OBJKT", s.hicetnuncMinterAddress) : option(contract(mintParams))) of
        | None -> (failwith("No minter found") : contract(mintParams))
        | Some(con) -> con
        end;

    const callToHic : operation = Tezos.transaction(p, 0tez, hicReceiver);

} with (list[callToHic], s)


function swap(var s : storage; var p : swapParams) : (list(operation) * storage) is
block {
    if (Tezos.sender = s.administrator) then skip
        else failwith("swap can call only administrator");

    const hicReceiver : contract(swapParams) =
        case (Tezos.get_entrypoint_opt("%swap", s.hicetnuncMinterAddress) : option(contract(swapParams))) of
        | None -> (failwith("No minter found") : contract(swapParams))
        | Some(con) -> con
        end;

    const callToHic : operation = Tezos.transaction(p, 0tez, hicReceiver);

} with (list[callToHic], s)


function getReceiver(var a : address) : contract(unit) is
    case (Tezos.get_contract_opt(a): option(contract(unit))) of
    | Some (con) -> con
    | None -> (failwith ("Not a contract") : (contract(unit)))
    end;


function default(var s : storage) : (list(operation) * storage) is
block {
    var operations : list(operation) := nil;
    for participantAddress -> participantShare in map s.shares block {
        const payoutAmount : tez = Tezos.amount * participantShare / 1000n;

        const receiver : contract(unit) = getReceiver(participantAddress);
        const op : operation = Tezos.transaction(unit, payoutAmount, receiver);
        operations := op # operations
    }
} with (operations, s)


function main (var params : action; var s : storage) : (list(operation) * storage) is
case params of
| Mint_OBJKT(p) -> mint(s, p)
| Swap(p) -> swap(s, p)
| Default -> default(s)
end

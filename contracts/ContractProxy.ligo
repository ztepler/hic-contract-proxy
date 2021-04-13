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


type account is record [
    (* share value would be nat that in sum should be equal to 1000 *)
    share : nat;

    (* withdrawalsSum is the sum that already withdrawn from contract by this participant *)
    withdrawalsSum : tez;
]


type action is
| Mint of mintParams
| Swap of swapParams
| Withdraw of unit
| Default of unit


type storage is record [
    (* administrator is originator of the contract, this is the only one who can call mint *)
    administrator : address;

    (* account is map of all participants with their shares and the sum, that rhey already withdrawn *)
    accounts : big_map(address, account);

    (* totalWithdrawalsSum is the total amount of all withdrawals from all of the participants *)
    totalWithdrawalsSum : tez;

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


function getAccount(var participant : address; var s : storage) : account is
case Big_map.find_opt(participant, s.accounts) of
| Some(acc) -> acc
| None -> record[ share = 0n; withdrawalsSum = 0tez ]
end;


function withdraw(var s : storage) : (list(operation) * storage) is
block {

    const totalRevenue = Tezos.balance + s.totalWithdrawalsSum;

    var participant : account := getAccount(Tezos.sender, s);

    (* NOTE: there are can be not equal division, what would happen? *)
    const totalParticipantEarnings = participant.share * totalRevenue / 1000n;
    const payoutAmount = totalParticipantEarnings - participant.withdrawalsSum;

    if (payoutAmount = 0tez) then failwith("Nothing to withdraw") else skip;

    const receiver : contract(unit) = getReceiver(Tezos.sender);
    const payoutOperation : operation = Tezos.transaction(unit, payoutAmount, receiver);

    s.totalWithdrawalsSum := s.totalWithdrawalsSum + payoutAmount;
    participant.withdrawalsSum := participant.withdrawalsSum + payoutAmount;
    s.accounts[Tezos.sender] := participant

} with (list[payoutOperation], s)


function main (var params : action; var s : storage) : (list(operation) * storage) is
case params of
| Mint(p) -> mint(s, p)
| Swap(p) -> swap(s, p)
| Withdraw -> withdraw(s)
| Default -> ((nil: list(operation)), s)
end

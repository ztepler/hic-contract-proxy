(* Including hic et nunc interface: *)
#include "../partials/hicetnunc.ligo"


(* Including common functions: *)
#include "../partials/general.ligo"


type account is record [
    (* share value would be nat that in sum should be equal to 1000 *)
    share : nat;

    (* withdrawalsSum is the sum that already withdrawn from contract by this participant *)
    withdrawalsSum : nat;
]


type action is
| Mint_OBJKT of mintParams
| Swap of swapParams
| Withdraw of unit
| Default of unit


type storage is record [
    (* administrator is originator of the contract, this is the only one who can call mint *)
    administrator : address;

    (* account is map of all participants with their shares and the sum, that rhey already withdrawn *)
    accounts : big_map(address, account);

    (* totalWithdrawalsSum is the total amount of all withdrawals from all of the participants *)
    totalWithdrawalsSum : nat;

    (* address of the Hic Et Nunc Minter (mainnet: KT1Hkg5qeNhfwpKW4fXvq7HGZB9z2EnmCCA9) *)
    minterAddress : address;

    (* address of the Hic Et Nunc Marketplace (mainnet: KT1HbQepzV1nVGg8QVznG7z4RcHseD5kwqBn) *)
    marketplaceAddress : address;
]


function getAccount(var participant : address; var s : storage) : account is
case Big_map.find_opt(participant, s.accounts) of [
| Some(acc) -> acc
| None -> record[ share = 0n; withdrawalsSum = 0n ]
];


function withdraw(var s : storage) : (list(operation) * storage) is
block {

    const totalRevenue = tezToNat(Tezos.balance) + s.totalWithdrawalsSum;

    var participant : account := getAccount(Tezos.sender, s);

    (* NOTE: there are can be not equal division, what would happen? *)
    const totalParticipantEarnings = participant.share * totalRevenue / 1000n;
    (* TODO: assert that participant.withdrawalsSum <= totalParticipantEarnings *)
    const payoutAmount = abs(totalParticipantEarnings - participant.withdrawalsSum);

    if (payoutAmount = 0n) then failwith("Nothing to withdraw") else skip;

    const receiver : contract(unit) = getReceiver(Tezos.sender);
    const payout = natToTez(payoutAmount);
    const payoutOperation : operation = Tezos.transaction(unit, payout, receiver);

    s.totalWithdrawalsSum := s.totalWithdrawalsSum + payoutAmount;
    participant.withdrawalsSum := participant.withdrawalsSum + payoutAmount;
    s.accounts[Tezos.sender] := participant

} with (list[payoutOperation], s)


function checkSenderIsAdmin(var store : storage) : unit is
    if (Tezos.sender = store.administrator) then unit
    else failwith("Entrypoint can call only administrator");


function mint_OBJKT(var store : storage; var params : mintParams) : (list(operation) * storage) is
block {
    checkSenderIsAdmin(store);
    const callToHic = callMintOBJKT(store.minterAddress, params);
} with (list[callToHic], store)


function swap(var store : storage; var params : swapParams) : (list(operation) * storage) is
block {
    checkSenderIsAdmin(store);
    const callToHic = callSwap(store.marketplaceAddress, params);
} with (list[callToHic], store)


function main (var params : action; var store : storage) : (list(operation) * storage) is
case params of [
| Mint_OBJKT(p) -> mint_OBJKT(store, p)
| Swap(p) -> swap(store, p)
| Withdraw -> withdraw(store)
| Default -> ((nil: list(operation)), store)
]

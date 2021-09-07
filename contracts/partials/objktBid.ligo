(*
type auctionParamsType is
    record [
        artist : address;
        end_time : timestamp;
        extension_time : nat;
        fa2 : address;
        objkt_id : nat;
        price_increment : tez;
        reserve : tez;
        royalties : nat;
        start_time : timestamp;
    ]
*)

// no comments:
type auctionParamsType is michelson_pair(
    michelson_pair(
        michelson_pair(address, "artist", timestamp, "end_time"),
        "",
        michelson_pair(nat, "extension_time", address, "fa2"),
        ""
    ),
    "",
    michelson_pair(
        michelson_pair(nat, "objkt_id", tez, "price_increment"),
        "",
        michelson_pair(
            tez,
            "reserve",
            michelson_pair(nat, "royalties", timestamp, "start_time"),
            ""
        ),
        ""
    ),
    ""
)

type placeEnglishParams is record [
    auctionParams : auctionParamsType;
    auctionAddress : address;
]

function callPlaceEnglish(
    const auctionAddress : address;
    const params : auctionParamsType) : operation is

block {
    const receiver : contract(auctionParamsType) =
        case (Tezos.get_entrypoint_opt("%create_auction", auctionAddress)
            : option(contract(auctionParamsType))) of
        | None -> (failwith("No auction found") : contract(auctionParamsType))
        | Some(con) -> con
        end;

    const callToAuction : operation = Tezos.transaction(params, 0tez, receiver);

} with callToAuction;


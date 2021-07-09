type operatorParam is
    [@layout:comb]
    record [
        owner : address;
        operator : address;
        token_id : nat;
    ]

type updateAction is
| Add_operator of operatorParam
| Remove_operator of operatorParam

type updateOperatorParam is updateAction
type updateOperatorsParam is list(updateOperatorParam)


function callUpdateOperators(
    const tokenAddress : address;
    const params : updateOperatorsParam) : operation is

block {
    const receiver : contract(updateOperatorsParam) =
        case (Tezos.get_entrypoint_opt("%update_operators", tokenAddress)
            : option(contract(updateOperatorsParam))) of
        | None -> (failwith("No FA2 contract found") : contract(updateOperatorsParam))
        | Some(con) -> con
        end;

    const callToFa2 : operation = Tezos.transaction(params, 0tez, receiver);

} with callToFa2;

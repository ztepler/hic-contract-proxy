function callAcceptOwnership(const galleryAddress : address) : operation is
block {
    const receiver : contract(unit) =
        case (Tezos.get_entrypoint_opt("%accept_ownership", galleryAddress)
            : option(contract(unit))) of
        | None -> (failwith("No gallery found") : contract(unit))
        | Some(con) -> con
        end;

    const acceptCall = Tezos.transaction(Unit, 0tez, receiver);
} with acceptCall


function callUpdateAdmin(const galleryAddress : address; const newAdminAddress : address) : operation is
block {
    const receiver : contract(address) =
        case (Tezos.get_entrypoint_opt("%update_admin", galleryAddress)
            : option(contract(address))) of
        | None -> (failwith("No gallery found") : contract(address))
        | Some(con) -> con
        end;

    const acceptCall = Tezos.transaction(newAdminAddress, 0tez, receiver);
} with acceptCall


(* isParticipantCore & isParticipantAdministrator
    - request have address type
    - response have bool type
    - params are address*contract(bool)
 *)
type isParticipantParams is record [
    participantAddress: address;
    callback: contract(bool);
]

(* getTotalShares have no request payload and returns nat
    so it just have this contract(nat) request params: *)
type getTotalSharesParams is contract(nat);

(* getParticipantShares request address and returns nat: *)
type getParticipantShares is record [
    participantAddress: address;
    callback: contract(nat);
]

type isMintedHashParams is record [
    metadata: bytes;
    callback: contract(bool);
]

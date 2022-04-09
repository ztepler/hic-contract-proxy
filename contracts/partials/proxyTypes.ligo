type participantRec is record [
    (* share is the fraction that participant would receive from every sale *)
    share : nat;

    (* role isCore allow participant to sign as one of the creator *)
    isCore : bool;
]

type participantsMap is map(address, participantRec);


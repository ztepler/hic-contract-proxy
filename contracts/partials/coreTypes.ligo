type executableCall is unit -> list(operation)

type originationResult is record [
    operation : operation;
    address : address;
    metadata : bytes;
]

type executableCall is bytes -> list(operation)

type originationResult is record [
    operation : operation;
    address : address;
    metadata : bytes;
]

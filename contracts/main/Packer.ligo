#include "../partials/hicetnunc.ligo"

type action is
| Mint_OBJKT of mintParams

function mint_OBJKT(var params : mintParams) : bytes is Bytes.pack(params)

function main (var params : action; var store : bytes) : (list(operation) * bytes) is
case params of
| Mint_OBJKT(p) -> ((nil: list(operation)), mint_OBJKT(p))
end

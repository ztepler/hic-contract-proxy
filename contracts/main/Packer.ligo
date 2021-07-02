#include "../partials/hicetnunc.ligo"
#include "../lambdas/originate/hicProxy.ligo"

type action is
| Mint_OBJKT of mintParams
| Originate_hic_proxy of participantsMap

function mint_OBJKT(var params : mintParams) : bytes is Bytes.pack(params)
function originate_hic_proxy(var params : participantsMap) : bytes is Bytes.pack(params)

function main (var params : action; var store : bytes) : (list(operation) * bytes) is
case params of
| Mint_OBJKT(p) -> ((nil: list(operation)), mint_OBJKT(p))
| Originate_hic_proxy(p) -> ((nil: list(operation)), originate_hic_proxy(p))
end

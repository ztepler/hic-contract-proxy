docker run --rm -v "$PWD":"$PWD" -w "$PWD" ligolang/ligo:0.39.0 compile contract contracts/main/HicProxy.ligo -e main --protocol hangzhou > build/tz/hic_proxy.tz
docker run --rm -v "$PWD":"$PWD" -w "$PWD" ligolang/ligo:0.39.0 compile contract contracts/main/BasicProxy.ligo -e main --protocol hangzhou > build/tz/basic_proxy.tz
docker run --rm -v "$PWD":"$PWD" -w "$PWD" ligolang/ligo:0.39.0 compile contract contracts/main/ContractProxyBigMap.ligo -e main --protocol hangzhou > build/tz/contract_proxy_bigmap.tz
docker run --rm -v "$PWD":"$PWD" -w "$PWD" ligolang/ligo:0.39.0 compile contract contracts/main/Factory.ligo -e main --protocol hangzhou > build/tz/factory.tz
docker run --rm -v "$PWD":"$PWD" -w "$PWD" ligolang/ligo:0.39.0 compile contract contracts/main/Sign.ligo -e main --protocol hangzhou > build/tz/sign.tz
docker run --rm -v "$PWD":"$PWD" -w "$PWD" ligolang/ligo:0.39.0 compile contract contracts/main/Packer.ligo -e main --protocol hangzhou > build/tz/packer.tz
docker run --rm -v "$PWD":"$PWD" -w "$PWD" ligolang/ligo:0.39.0 compile contract contracts/main/SwapAdmin.ligo -e main --protocol hangzhou > build/tz/swap_admin.tz
docker run --rm -v "$PWD":"$PWD" -w "$PWD" ligolang/ligo:0.39.0 compile contract contracts/main/MockView.ligo -e main > build/tz/mock_view.tz
docker run --rm -v "$PWD":"$PWD" -w "$PWD" ligolang/ligo:0.39.0 compile expression pascaligo lambda --init-file "contracts/lambdas/call/hicMintOBJKT.ligo" > build/tz/lambdas/call/hic_mint_OBJKT.tz
docker run --rm -v "$PWD":"$PWD" -w "$PWD" ligolang/ligo:0.39.0 compile expression pascaligo lambda --init-file "contracts/lambdas/originate/hicProxy.ligo" > build/tz/lambdas/originate/hic_proxy.tz
docker run --rm -v "$PWD":"$PWD" -w "$PWD" ligolang/ligo:0.39.0 compile expression pascaligo lambda --init-file "contracts/lambdas/originate/basicProxy.ligo" > build/tz/lambdas/originate/basic_proxy.tz
docker run --rm -v "$PWD":"$PWD" -w "$PWD" ligolang/ligo:0.39.0 compile expression pascaligo lambda --init-file "contracts/lambdas/call/teiaMarketplaceSwap.ligo" > build/tz/lambdas/call/teia_marketplace_swap.tz
docker run --rm -v "$PWD":"$PWD" -w "$PWD" ligolang/ligo:0.39.0 compile expression pascaligo lambda --init-file "contracts/lambdas/call/teiaMarketplaceCancelSwap.ligo" > build/tz/lambdas/call/teia_marketplace_cancel_swap.tz
docker run --rm -v "$PWD":"$PWD" -w "$PWD" ligolang/ligo:0.39.0 compile expression pascaligo lambda --init-file "contracts/lambdas/call/teiaMarketplaceSwap.ligo" --michelson-format json > build/tz/lambdas/call/teiaMarketplaceSwap.json
docker run --rm -v "$PWD":"$PWD" -w "$PWD" ligolang/ligo:0.39.0 compile expression pascaligo lambda --init-file "contracts/lambdas/call/teiaMarketplaceCancelSwap.ligo" --michelson-format json > build/tz/lambdas/call/teiaMarketplaceCancelSwap.json
pytest -v

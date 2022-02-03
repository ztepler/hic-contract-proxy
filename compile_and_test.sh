docker run --rm -v "$PWD":"$PWD" -w "$PWD" ligolang/ligo:0.29.0 compile contract contracts/main/FxHashProxy.ligo -e main > build/tz/fxhash_proxy.tz
docker run --rm -v "$PWD":"$PWD" -w "$PWD" ligolang/ligo:0.24.0 compile-contract contracts/main/HicProxy.ligo main > build/tz/hic_proxy.tz
docker run --rm -v "$PWD":"$PWD" -w "$PWD" ligolang/ligo:0.24.0 compile-contract contracts/main/BasicProxy.ligo main > build/tz/basic_proxy.tz
docker run --rm -v "$PWD":"$PWD" -w "$PWD" ligolang/ligo:0.24.0 compile-contract contracts/main/ContractProxyBigMap.ligo main > build/tz/contract_proxy_bigmap.tz
docker run --rm -v "$PWD":"$PWD" -w "$PWD" ligolang/ligo:0.24.0 compile-contract contracts/main/Factory.ligo main > build/tz/factory.tz
docker run --rm -v "$PWD":"$PWD" -w "$PWD" ligolang/ligo:0.24.0 compile-contract contracts/main/Sign.ligo main > build/tz/sign.tz
docker run --rm -v "$PWD":"$PWD" -w "$PWD" ligolang/ligo:0.24.0 compile-contract contracts/main/Packer.ligo main > build/tz/packer.tz
docker run --rm -v "$PWD":"$PWD" -w "$PWD" ligolang/ligo:0.24.0 compile-contract contracts/main/SwapAdmin.ligo main > build/tz/swap_admin.tz
docker run --rm -v "$PWD":"$PWD" -w "$PWD" ligolang/ligo:0.24.0 compile-expression pascaligo --init-file="contracts/lambdas/call/hicMintOBJKT.ligo" lambda > build/tz/lambdas/call/hic_mint_OBJKT.tz
docker run --rm -v "$PWD":"$PWD" -w "$PWD" ligolang/ligo:0.24.0 compile-expression pascaligo --init-file="contracts/lambdas/originate/hicProxy.ligo" lambda > build/tz/lambdas/originate/hic_proxy.tz
docker run --rm -v "$PWD":"$PWD" -w "$PWD" ligolang/ligo:0.24.0 compile-expression pascaligo --init-file="contracts/lambdas/originate/basicProxy.ligo" lambda > build/tz/lambdas/originate/basic_proxy.tz
docker run --rm -v "$PWD":"$PWD" -w "$PWD" ligolang/ligo:0.24.0 compile-contract contracts/main/MockView.ligo main > build/tz/mock_view.tz
docker run --rm -v "$PWD":"$PWD" -w "$PWD" ligolang/ligo:0.31.0 compile expression pascaligo lambda --init-file "contracts/lambdas/call/marketplaceV3Swap.ligo" > build/tz/lambdas/call/marketplace_v3_swap.tz
docker run --rm -v "$PWD":"$PWD" -w "$PWD" ligolang/ligo:0.31.0 compile expression pascaligo lambda --init-file "contracts/lambdas/call/marketplaceV3CancelSwap.ligo" > build/tz/lambdas/call/marketplace_v3_cancel_swap.tz
pytest -v


docker run --rm -v "$PWD":"$PWD" -w "$PWD" ligolang/ligo:0.13.0 compile-contract contracts/main/LambdaProxy.ligo main > build/tz/lambda_proxy.tz
docker run --rm -v "$PWD":"$PWD" -w "$PWD" ligolang/ligo:0.13.0 compile-contract contracts/main/LambdaFactory.ligo main > build/tz/lambda_factory.tz
docker run --rm -v "$PWD":"$PWD" -w "$PWD" ligolang/ligo:0.13.0 compile-contract contracts/main/ContractProxyBigMap.ligo main > build/tz/contract_proxy_bigmap.tz
docker run --rm -v "$PWD":"$PWD" -w "$PWD" ligolang/ligo:0.13.0 compile-contract contracts/main/ContractProxyMap.ligo main > build/tz/contract_proxy_map.tz
docker run --rm -v "$PWD":"$PWD" -w "$PWD" ligolang/ligo:0.13.0 compile-contract contracts/main/Factory.ligo main > build/tz/factory.tz
docker run --rm -v "$PWD":"$PWD" -w "$PWD" ligolang/ligo:0.13.0 compile-contract contracts/main/Sign.ligo main > build/tz/sign.tz
pytest -v


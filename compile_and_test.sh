docker run --rm -v "$PWD":"$PWD" -w "$PWD" ligolang/ligo:0.13.0 compile-contract contracts/main/ContractProxyBigMap.ligo main > pytezos_tests/contract_proxy_bigmap.tz
docker run --rm -v "$PWD":"$PWD" -w "$PWD" ligolang/ligo:0.13.0 compile-contract contracts/main/ContractProxyMap.ligo main > pytezos_tests/contract_proxy_map.tz
docker run --rm -v "$PWD":"$PWD" -w "$PWD" ligolang/ligo:0.13.0 compile-contract contracts/main/Factory.ligo main > pytezos_tests/factory.tz
pytest -v


const ContractProxy = artifacts.require("ContractProxyMap");
const { MichelsonMap } = require("@taquito/taquito");
const { pkh } = require("../faucet.json");

const initialStorage = {
  administrator: pkh,
  shares: MichelsonMap.fromLiteral({
    tz1iQE8ijR5xVPffBUPFubwB9XQJuyD9qsoJ: 330,
    tz1MdaJfWzP5pPx3gwPxfdLZTHW6js9havos: 670,
  }),
  totalShares: 1000,
  hicetnuncMinterAddress: "KT1Hkg5qeNhfwpKW4fXvq7HGZB9z2EnmCCA9",
};

module.exports = deployer => {
  deployer.deploy(ContractProxy, initialStorage);
};


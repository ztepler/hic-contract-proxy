const ContractProxy = artifacts.require("ContractProxy");
const { MichelsonMap } = require("@taquito/taquito");
const { pkh } = require("../faucet.json");

const initialStorage = {
  administrator: pkh,
  accounts: MichelsonMap.fromLiteral({
    tz1iQE8ijR5xVPffBUPFubwB9XQJuyD9qsoJ: {share: 330, withdrawalsSum: 0},
    tz1MdaJfWzP5pPx3gwPxfdLZTHW6js9havos: {share: 670, withdrawalsSum: 0},
  }),
  totalWithdrawalsSum: 0,
  hicetnuncMinterAddress: "KT1Hkg5qeNhfwpKW4fXvq7HGZB9z2EnmCCA9",
};

module.exports = deployer => {
  deployer.deploy(ContractProxy, initialStorage);
};


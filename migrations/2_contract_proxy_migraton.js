const ContractProxy = artifacts.require("ContractProxy");
const { MichelsonMap } = require("@taquito/taquito");
const { pkh } = require("../faucet.json");

const initialStorage = {
  administrator: pkh,
  accounts: MichelsonMap.fromLiteral({
    tz1f94uZ7SF2fLKnMjFzGQTbznd8qpAZ12is: {share: 330, withdrawalsSum: 0},
    tz1NvGRKVwoihihAubacMHrDrd2uM6tumrZv: {share: 670, withdrawalsSum: 0},
  }),
  totalWithdrawalsSum: 0,
  hicetnuncMinterAddress: "KT1Hkg5qeNhfwpKW4fXvq7HGZB9z2EnmCCA9",
};

module.exports = deployer => {
  deployer.deploy(ContractProxy, initialStorage);
};


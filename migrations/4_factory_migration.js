const Factory = artifacts.require("Factory");

const initialStorage = {
  originatedContracts: 0,
  hicetnuncMinterAddress: 'KT1Hkg5qeNhfwpKW4fXvq7HGZB9z2EnmCCA9'
};

module.exports = deployer => {
  deployer.deploy(Factory, initialStorage);
};


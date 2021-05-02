const { mnemonic, secret, password, email } = require("./faucet.json");

module.exports = {
  contracts_directory: "./contracts/main",
  networks: {
    mainnet: {
      host: "https://mainnet.smartpy.io",
      port: 443,
      network_id: "*",
      type: "tezos"
    },
    development: {
      host: "https://florencenet.smartpy.io",
      port: 443,
      network_id: "*",
      secret,
      mnemonic,
      password,
      email,
      type: "tezos"
    }
  }
};

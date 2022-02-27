from brownie import (
    accounts,
    network,
    config,
)

LOCAL_BLOCKCHAIN_ENVIRONMENTS = ["mainnet-fork-dev", "development", "ganache-local"]


def get_account(index=0, id=None):
    if index:
        return accounts[index]
    if id:
        return accounts.load(id)

    if network.show_active() in LOCAL_BLOCKCHAIN_ENVIRONMENTS:
        return accounts[0]

    return accounts.add(config["wallets"]["from_key"])

from brownie import interface, config, network
from scripts.utils import get_account


def main():
    get_weth()


def get_weth():
    """
    Mints WETH by depositing ETH
    """
    # ABI
    # Address
    account = get_account()
    weth = interface.IWeth(config["networks"][network.show_active()]["weth_token"])
    # Refer here to see the transation(writeable) functions https://kovan.etherscan.io/token/0xd0a1e359811322d97991e03f863a0c30c2cf029c#writeContract
    tx = weth.deposit({"from": account, "value": 0.1 * 10**18})
    tx.wait(1)
    print("Received 0.1 WETH")

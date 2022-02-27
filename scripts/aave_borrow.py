from brownie import interface, config, network
from scripts.get_weth import get_weth
from scripts.utils import get_account
from web3 import Web3

# 0.1
AMOUNT = Web3.toWei(0.1, "ether")


def main():
    account = get_account()
    active_network = network.show_active()
    erc20_address = config["networks"][active_network]["weth_token"]

    if active_network in ["mainnet-fork-dev"]:
        get_weth()

    lending_pool = get_lending_pool()
    # Approve sending ERC 20 tokens
    approve_erc20(AMOUNT, lending_pool.address, erc20_address, account)
    # function deposit(address asset, uint256 amount, address onBehalfOf, uint16 referralCode)
    print("Depositing...")
    tx = lending_pool.deposit(erc20_address, AMOUNT, account, 0, {"from": account})
    tx.wait(1)
    print("Deposited!")

    # After depositing we can now borrow against it?
    # To ensure we have a positive health factor
    borrowable_eth, total_debt = get_borrowable_data(lending_pool, account)
    # DAI in terms of ETH
    print("Lets Borrow...")
    dai_eth_price = get_asset_price(
        config["networks"][active_network]["dai_eth_price_feed"]
    )
    # We multiply by 0.95 for a better Health Factor
    amount_dai_to_borrow = (1 / dai_eth_price) * (borrowable_eth * 0.95)
    # borrowable_eth -> borrowable_dai * 95% => To ensure we don't get liquidated easily
    print(f"We are gonna borrow {amount_dai_to_borrow} DAI")
    # Now Borrow
    # https://docs.aave.com/developers/v/2.0/the-core-protocol/lendingpool#borrow
    dai_address = config["networks"][active_network]["dai_token"]
    borrow_tx = lending_pool.borrow(
        dai_address,
        Web3.toWei(amount_dai_to_borrow, "ether"),
        1,
        0,
        account,
        {"from": account},
    )
    borrow_tx.wait(1)
    print("We borrowed some DAI")
    get_borrowable_data(lending_pool, account)

    repay_all(AMOUNT, lending_pool, account)

    print(
        "YOU just DEPOSITED => BORROWED => AND REPAID with AAVE, Brownie and Chainlink!!!"
    )


def get_lending_pool():
    # ABI, Address
    lending_pool_addresses_provider = interface.ILendingPoolAddressesProvider(
        config["networks"][network.show_active()]["lending_pool_addresses_provider"]
    )
    # https://docs.aave.com/developers/v/2.0/the-core-protocol/addresses-provider#getlendingpool
    lending_pool_address = lending_pool_addresses_provider.getLendingPool()
    lending_pool = interface.ILendingPool(lending_pool_address)
    return lending_pool


def approve_erc20(amount, spender, erc20_address, account):
    print("Approving ERC20 token")
    erc20 = interface.IERC20(erc20_address)
    print("Token Name", erc20.name())
    tx = erc20.approve(spender, amount, {"from": account})
    tx.wait(1)
    print("Approved!")
    return tx


def get_borrowable_data(lending_pool, account):
    (
        total_collateral_eth,
        total_debt_eth,
        available_borrow_eth,
        current_liquidation_threshold,
        ltv,
        health_factor,
    ) = lending_pool.getUserAccountData(account)

    available_borrow_eth = Web3.fromWei(available_borrow_eth, "ether")
    total_collateral_eth = Web3.fromWei(total_collateral_eth, "ether")
    total_debt_eth = Web3.fromWei(total_debt_eth, "ether")

    print(f"You have {total_collateral_eth} worth of ETH deposited.")
    print(f"You have {total_debt_eth} worth of ETH borrowed.")
    print(f"You can borrow {available_borrow_eth} worth of ETH.")

    return (float(available_borrow_eth), float(total_debt_eth))


def get_asset_price(price_feed_address):
    # ABI, Address
    price_feed = interface.IAggregatorV3Interface(price_feed_address)
    # We only want the 1st index of response which is the latest price
    latest_price = price_feed.latestRoundData()[1]
    converted_latest_price = Web3.fromWei(latest_price, "ether")
    print(f"The ASSET to ETH price is {converted_latest_price}")
    return float(converted_latest_price)


def repay_all(amount, lending_pool, account):
    dai_token = config["networks"][network.show_active()]["dai_token"]
    approve_erc20(amount, lending_pool.address, dai_token, account)

    # https://docs.aave.com/developers/v/2.0/the-core-protocol/lendingpool#repay
    # function repay(address asset, uint256 amount, uint256 rateMode, address onBehalfOf)
    repay_tx = lending_pool.repay(dai_token, amount, 1, account, {"from": account})
    repay_tx.wait(1)
    print("Repaid!")

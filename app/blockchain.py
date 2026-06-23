from decimal import Decimal

from web3 import Web3
from web3.exceptions import TimeExhausted

try:
    from app.config import get_config
except ModuleNotFoundError:
    from config import get_config


def get_web3():
    """Create Web3 connection to Sepolia RPC."""
    config = get_config()
    w3 = Web3(Web3.HTTPProvider(config["rpc_url"]))
    return w3


def get_contracts():
    """Load Web3 connection and contract objects."""
    config = get_config()
    w3 = get_web3()

    lending_pool = w3.eth.contract(
        address=Web3.to_checksum_address(config["lending_pool_address"]),
        abi=config["lending_pool_abi"],
    )

    mock_usd = w3.eth.contract(
        address=Web3.to_checksum_address(config["mock_usd_address"]),
        abi=config["mock_usd_abi"],
    )

    return w3, config, lending_pool, mock_usd


def wei_to_eth(value_wei):
    """Convert wei to ETH as Decimal."""
    return Decimal(value_wei) / Decimal(10**18)


def token_to_decimal(value, decimals=18):
    """Convert token raw unit to decimal value."""
    return Decimal(value) / Decimal(10**decimals)


def format_decimal(value, places=6):
    """Format Decimal for display."""
    value = Decimal(value)
    return f"{value:,.{places}f}"


def get_eth_price_from_lending_pool(lending_pool):
    """
    Read ETH/USD price from LendingPool.

    Expected getETHPrice() return:
    - price
    - decimals
    - updatedAt

    But this function also supports the case where only price is returned.
    """
    result = lending_pool.functions.getETHPrice().call()

    if isinstance(result, list) or isinstance(result, tuple):
        price_raw = result[0]
        decimals = result[1] if len(result) > 1 else 8
        updated_at = result[2] if len(result) > 2 else None
    else:
        price_raw = result
        decimals = 8
        updated_at = None

    price = Decimal(price_raw) / Decimal(10**decimals)

    return {
        "price_raw": price_raw,
        "decimals": decimals,
        "updated_at": updated_at,
        "price": price,
    }


def read_basic_status():
    """Read basic blockchain and contract status."""
    w3, config, lending_pool, mock_usd = get_contracts()

    is_connected = w3.is_connected()
    chain_id = w3.eth.chain_id if is_connected else None
    latest_block = w3.eth.block_number if is_connected else None

    eth_price = get_eth_price_from_lending_pool(lending_pool)

    mock_usd_name = mock_usd.functions.name().call()
    mock_usd_symbol = mock_usd.functions.symbol().call()

    return {
        "is_connected": is_connected,
        "chain_id": chain_id,
        "latest_block": latest_block,
        "network": config["network"],
        "deployer": config["deployer"],
        "lending_pool_address": config["lending_pool_address"],
        "mock_usd_address": config["mock_usd_address"],
        "price_feed_address": config["price_feed_address"],
        "eth_price": eth_price,
        "mock_usd_name": mock_usd_name,
        "mock_usd_symbol": mock_usd_symbol,
    }

def read_user_position(user_address=None):
    """
    Read wallet balance and lending position for one user.

    If user_address is None, use deployer address from contract_addresses.json.
    """
    w3, config, lending_pool, mock_usd = get_contracts()

    if user_address is None:
        user_address = config["deployer"]

    user_address = Web3.to_checksum_address(user_address)

    # Wallet balances
    eth_balance_wei = w3.eth.get_balance(user_address)
    mock_usd_balance_raw = mock_usd.functions.balanceOf(user_address).call()

    # Lending position from LendingPool
    loan_info = lending_pool.functions.getLoanInfo(user_address).call()

    collateral_eth_raw = loan_info[0]
    debt_mock_usd_raw = loan_info[1]
    collateral_value_usd_raw = loan_info[2]
    max_borrowable_usd_raw = loan_info[3]
    current_ltv_raw = loan_info[4]
    health_factor_raw = loan_info[5]

    return {
        "user_address": user_address,
        "eth_balance": wei_to_eth(eth_balance_wei),
        "mock_usd_balance": token_to_decimal(mock_usd_balance_raw, 18),
        "collateral_eth": wei_to_eth(collateral_eth_raw),
        "debt_mock_usd": token_to_decimal(debt_mock_usd_raw, 18),
        "collateral_value_usd": token_to_decimal(collateral_value_usd_raw, 18),
        "max_borrowable_usd": token_to_decimal(max_borrowable_usd_raw, 18),
        # Contract stores LTV in basis points.
        # Example: 2175 means 21.75%.
        "current_ltv_percent": token_to_decimal(current_ltv_raw, 18) * Decimal(100),
        "health_factor": token_to_decimal(health_factor_raw, 18),
    }


def get_loan_status_label(health_factor, debt):
    """Classify loan status for dashboard display."""
    health_factor = Decimal(health_factor)
    debt = Decimal(debt)

    if debt == 0:
        return "No debt"

    if health_factor >= Decimal("1.5"):
        return "Safe"

    if health_factor >= Decimal("1.0"):
        return "Warning"

    return "Liquidatable"

def get_signer_account():
    """Load signer account from PRIVATE_KEY in .env."""
    config = get_config()
    private_key = config.get("private_key")

    if not private_key:
        raise ValueError("Missing PRIVATE_KEY in .env. Cannot send transaction.")

    w3 = get_web3()
    account = w3.eth.account.from_key(private_key)

    return w3, config, account


def send_signed_transaction(w3, account, tx):
    """
    Sign and send a transaction.

    If the transaction receipt is not available before timeout,
    return the tx_hash as pending instead of raising an error.
    """
    signed_tx = w3.eth.account.sign_transaction(tx, private_key=account.key)

    raw_tx = getattr(signed_tx, "rawTransaction", None)
    if raw_tx is None:
        raw_tx = getattr(signed_tx, "raw_transaction")

    tx_hash = w3.eth.send_raw_transaction(raw_tx)

    tx_hash_hex = tx_hash.hex()
    if not tx_hash_hex.startswith("0x"):
        tx_hash_hex = "0x" + tx_hash_hex

    try:
        receipt = w3.eth.wait_for_transaction_receipt(tx_hash, timeout=300)

        return {
            "tx_hash": tx_hash_hex,
            "status": receipt.status,
            "block_number": receipt.blockNumber,
            "gas_used": receipt.gasUsed,
            "is_pending": False,
        }

    except TimeExhausted:
        return {
            "tx_hash": tx_hash_hex,
            "status": None,
            "block_number": None,
            "gas_used": None,
            "is_pending": True,
        }

def deposit_collateral(amount_eth):
    """
    Send depositCollateral() transaction to LendingPool.

    amount_eth example:
    "0.0001"
    """
    w3, config, lending_pool, mock_usd = get_contracts()
    _, _, account = get_signer_account()

    amount_wei = w3.to_wei(str(amount_eth), "ether")

    tx = lending_pool.functions.depositCollateral().build_transaction(
        {
            "from": account.address,
            "value": amount_wei,
            "nonce": w3.eth.get_transaction_count(account.address),
            "chainId": config["chain_id"],
            "gas": 200000,
            "gasPrice": w3.eth.gas_price,
        }
    )

    return send_signed_transaction(w3, account, tx)

def borrow_mock_usd(amount_mock_usd):
    """
    Send borrow(amount) transaction to LendingPool.

    amount_mock_usd example:
    "0.1"

    MockUSD uses 18 decimals, so we convert the input amount
    to raw token units using 10^18.
    """
    w3, config, lending_pool, mock_usd = get_contracts()
    _, _, account = get_signer_account()

    amount_raw = w3.to_wei(str(amount_mock_usd), "ether")

    tx = lending_pool.functions.borrow(amount_raw).build_transaction(
        {
            "from": account.address,
            "nonce": w3.eth.get_transaction_count(account.address),
            "chainId": config["chain_id"],
            "gas": 250000,
            "gasPrice": w3.eth.gas_price,
        }
    )

    return send_signed_transaction(w3, account, tx)

def repay_mock_usd(amount_mock_usd):
    """
    Send approve() and repay(amount) transactions.

    Repay requires two blockchain transactions:
    1. Approve LendingPool to spend MockUSD
    2. Call LendingPool.repay(amount)
    """
    w3, config, lending_pool, mock_usd = get_contracts()
    _, _, account = get_signer_account()

    amount_raw = w3.to_wei(str(amount_mock_usd), "ether")

    approve_tx = mock_usd.functions.approve(
        Web3.to_checksum_address(config["lending_pool_address"]),
        amount_raw,
    ).build_transaction(
        {
            "from": account.address,
            "nonce": w3.eth.get_transaction_count(account.address),
            "chainId": config["chain_id"],
            "gas": 100000,
            "gasPrice": w3.eth.gas_price,
        }
    )

    approve_receipt = send_signed_transaction(w3, account, approve_tx)

    if approve_receipt["status"] != 1:
        return {
            "approve": approve_receipt,
            "repay": None,
            "success": False,
            "message": "Approve transaction was not confirmed successfully.",
        }

    repay_tx = lending_pool.functions.repay(amount_raw).build_transaction(
        {
            "from": account.address,
            "nonce": w3.eth.get_transaction_count(account.address),
            "chainId": config["chain_id"],
            "gas": 250000,
            "gasPrice": w3.eth.gas_price,
        }
    )

    repay_receipt = send_signed_transaction(w3, account, repay_tx)

    return {
        "approve": approve_receipt,
        "repay": repay_receipt,
        "success": repay_receipt["status"] == 1,
        "message": "Repay completed." if repay_receipt["status"] == 1 else "Repay was sent but not confirmed successfully.",
    }

def withdraw_collateral(amount_eth):
    """
    Send withdrawCollateral(amount) transaction to LendingPool.

    amount_eth example:
    "0.0001"

    The transaction will revert if withdrawing this amount makes
    the loan unsafe.
    """
    w3, config, lending_pool, mock_usd = get_contracts()
    _, _, account = get_signer_account()

    amount_wei = w3.to_wei(str(amount_eth), "ether")

    tx = lending_pool.functions.withdrawCollateral(amount_wei).build_transaction(
        {
            "from": account.address,
            "nonce": w3.eth.get_transaction_count(account.address),
            "chainId": config["chain_id"],
            "gas": 250000,
            "gasPrice": w3.eth.gas_price,
        }
    )

    return send_signed_transaction(w3, account, tx)

if __name__ == "__main__":
    status = read_basic_status()
    position = read_user_position()

    print("Blockchain connection test")
    print("--------------------------")
    print("Connected:", status["is_connected"])
    print("Network:", status["network"])
    print("Chain ID:", status["chain_id"])
    print("Latest block:", status["latest_block"])
    print("LendingPool:", status["lending_pool_address"])
    print("MockUSDToken:", status["mock_usd_address"])
    print("ETH/USD Price Feed:", status["price_feed_address"])
    print()

    print("ETH/USD price from LendingPool")
    print("Formatted price:", format_decimal(status["eth_price"]["price"], 8), "USD")
    print()

    print("User lending dashboard data")
    print("---------------------------")
    print("Wallet:", position["user_address"])
    print("Wallet ETH balance:", format_decimal(position["eth_balance"], 18), "ETH")
    print("Wallet MockUSD balance:", format_decimal(position["mock_usd_balance"], 18), "MockUSD")
    print("Collateral ETH:", format_decimal(position["collateral_eth"], 18), "ETH")
    print("Debt MockUSD:", format_decimal(position["debt_mock_usd"], 18), "MockUSD")
    print("Collateral Value USD:", format_decimal(position["collateral_value_usd"], 18), "USD")
    print("Max Borrowable USD:", format_decimal(position["max_borrowable_usd"], 18), "MockUSD")
    print("Current LTV:", format_decimal(position["current_ltv_percent"], 2), "%")
    print("Health Factor:", format_decimal(position["health_factor"], 12))
    print("Loan Status:", get_loan_status_label(position["health_factor"], position["debt_mock_usd"]))
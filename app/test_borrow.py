try:
    from app.blockchain import (
        borrow_mock_usd,
        read_user_position,
        format_decimal,
    )
except ModuleNotFoundError:
    from blockchain import (
        borrow_mock_usd,
        read_user_position,
        format_decimal,
    )


AMOUNT_MOCK_USD = "0.1"

print("Testing borrow MockUSD from Python/web3.py")
print("------------------------------------------")
print("Borrow amount:", AMOUNT_MOCK_USD, "MockUSD")
print()

before = read_user_position()

print("Before borrow")
print("Collateral ETH:", format_decimal(before["collateral_eth"], 18))
print("Debt MockUSD:", format_decimal(before["debt_mock_usd"], 18))
print("Max Borrowable USD:", format_decimal(before["max_borrowable_usd"], 18))
print("Current LTV:", format_decimal(before["current_ltv_percent"], 2), "%")
print("Health Factor:", format_decimal(before["health_factor"], 12))
print()

confirm = input("Type YES to send borrow transaction: ")

if confirm != "YES":
    print("Cancelled.")
    raise SystemExit

receipt = borrow_mock_usd(AMOUNT_MOCK_USD)

print()
print("Transaction sent.")
print("Tx hash:", receipt["tx_hash"])
print("Status:", receipt["status"])
print("Pending:", receipt.get("is_pending"))
print("Block number:", receipt["block_number"])
print("Gas used:", receipt["gas_used"])
print()

after = read_user_position()

print("After borrow")
print("Collateral ETH:", format_decimal(after["collateral_eth"], 18))
print("Debt MockUSD:", format_decimal(after["debt_mock_usd"], 18))
print("Wallet MockUSD balance:", format_decimal(after["mock_usd_balance"], 18))
print("Current LTV:", format_decimal(after["current_ltv_percent"], 2), "%")
print("Health Factor:", format_decimal(after["health_factor"], 12))
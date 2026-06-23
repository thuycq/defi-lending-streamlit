try:
    from app.blockchain import (
        repay_mock_usd,
        read_user_position,
        format_decimal,
    )
except ModuleNotFoundError:
    from blockchain import (
        repay_mock_usd,
        read_user_position,
        format_decimal,
    )


AMOUNT_MOCK_USD = "0.1"

print("Testing repay MockUSD from Python/web3.py")
print("-----------------------------------------")
print("Repay amount:", AMOUNT_MOCK_USD, "MockUSD")
print()

before = read_user_position()

print("Before repay")
print("Collateral ETH:", format_decimal(before["collateral_eth"], 18))
print("Debt MockUSD:", format_decimal(before["debt_mock_usd"], 18))
print("Wallet MockUSD balance:", format_decimal(before["mock_usd_balance"], 18))
print("Current LTV:", format_decimal(before["current_ltv_percent"], 2), "%")
print("Health Factor:", format_decimal(before["health_factor"], 12))
print()

confirm = input("Type YES to send approve + repay transactions: ")

if confirm != "YES":
    print("Cancelled.")
    raise SystemExit

result = repay_mock_usd(AMOUNT_MOCK_USD)

print()
print("Approve transaction")
print("-------------------")
print("Tx hash:", result["approve"]["tx_hash"])
print("Status:", result["approve"]["status"])
print("Pending:", result["approve"].get("is_pending"))
print("Block number:", result["approve"]["block_number"])
print("Gas used:", result["approve"]["gas_used"])
print()

if result["repay"] is not None:
    print("Repay transaction")
    print("-----------------")
    print("Tx hash:", result["repay"]["tx_hash"])
    print("Status:", result["repay"]["status"])
    print("Pending:", result["repay"].get("is_pending"))
    print("Block number:", result["repay"]["block_number"])
    print("Gas used:", result["repay"]["gas_used"])
    print()

print("Success:", result["success"])
print("Message:", result["message"])
print()

after = read_user_position()

print("After repay")
print("Collateral ETH:", format_decimal(after["collateral_eth"], 18))
print("Debt MockUSD:", format_decimal(after["debt_mock_usd"], 18))
print("Wallet MockUSD balance:", format_decimal(after["mock_usd_balance"], 18))
print("Current LTV:", format_decimal(after["current_ltv_percent"], 2), "%")
print("Health Factor:", format_decimal(after["health_factor"], 12))
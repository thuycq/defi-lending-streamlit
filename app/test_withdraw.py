try:
    from app.blockchain import (
        withdraw_collateral,
        read_user_position,
        format_decimal,
    )
except ModuleNotFoundError:
    from blockchain import (
        withdraw_collateral,
        read_user_position,
        format_decimal,
    )


AMOUNT_ETH = "0.0001"

print("Testing withdraw collateral from Python/web3.py")
print("------------------------------------------------")
print("Withdraw amount:", AMOUNT_ETH, "ETH")
print()

before = read_user_position()

print("Before withdraw")
print("Collateral ETH:", format_decimal(before["collateral_eth"], 18))
print("Debt MockUSD:", format_decimal(before["debt_mock_usd"], 18))
print("Collateral Value USD:", format_decimal(before["collateral_value_usd"], 18))
print("Current LTV:", format_decimal(before["current_ltv_percent"], 2), "%")
print("Health Factor:", format_decimal(before["health_factor"], 12))
print()

confirm = input("Type YES to send withdraw transaction: ")

if confirm != "YES":
    print("Cancelled.")
    raise SystemExit

receipt = withdraw_collateral(AMOUNT_ETH)

print()
print("Withdraw transaction")
print("--------------------")
print("Tx hash:", receipt["tx_hash"])
print("Status:", receipt["status"])
print("Pending:", receipt.get("is_pending"))
print("Block number:", receipt["block_number"])
print("Gas used:", receipt["gas_used"])
print()

after = read_user_position()

print("After withdraw")
print("Collateral ETH:", format_decimal(after["collateral_eth"], 18))
print("Debt MockUSD:", format_decimal(after["debt_mock_usd"], 18))
print("Collateral Value USD:", format_decimal(after["collateral_value_usd"], 18))
print("Current LTV:", format_decimal(after["current_ltv_percent"], 2), "%")
print("Health Factor:", format_decimal(after["health_factor"], 12))
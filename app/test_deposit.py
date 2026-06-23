try:
    from app.blockchain import deposit_collateral, read_user_position, format_decimal
except ModuleNotFoundError:
    from blockchain import deposit_collateral, read_user_position, format_decimal


AMOUNT_ETH = "0.0001"

print("Testing deposit collateral from Python/web3.py")
print("---------------------------------------------")
print("Deposit amount:", AMOUNT_ETH, "ETH")
print()

before = read_user_position()

print("Before deposit")
print("Collateral ETH:", format_decimal(before["collateral_eth"], 18))
print("Debt MockUSD:", format_decimal(before["debt_mock_usd"], 18))
print("Health Factor:", format_decimal(before["health_factor"], 12))
print()

confirm = input("Type YES to send deposit transaction: ")

if confirm != "YES":
    print("Cancelled.")
    raise SystemExit

receipt = deposit_collateral(AMOUNT_ETH)

print()
print("Transaction sent.")
print("Tx hash:", receipt["tx_hash"])
print("Status:", receipt["status"])
print("Block number:", receipt["block_number"])
print("Gas used:", receipt["gas_used"])
print()

after = read_user_position()

print("After deposit")
print("Collateral ETH:", format_decimal(after["collateral_eth"], 18))
print("Debt MockUSD:", format_decimal(after["debt_mock_usd"], 18))
print("Health Factor:", format_decimal(after["health_factor"], 12))
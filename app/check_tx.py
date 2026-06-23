from web3.exceptions import TransactionNotFound

try:
    from app.blockchain import get_web3
except ModuleNotFoundError:
    from blockchain import get_web3


TX_HASH = "0x7d95cee2f15d036d2730bdafec72d2aa59aea8818b236bc097649af5ad09a13a"


w3 = get_web3()

print("Checking transaction")
print("--------------------")
print("Connected:", w3.is_connected())
print("Tx hash:", TX_HASH)
print()

try:
    tx = w3.eth.get_transaction(TX_HASH)

    print("Transaction found.")
    print("From:", tx["from"])
    print("To:", tx["to"])
    print("Nonce:", tx["nonce"])
    print("Block number:", tx["blockNumber"])
    print("Gas price:", tx.get("gasPrice"))
    print()

except TransactionNotFound:
    print("Transaction not found by RPC.")
    print("It may be dropped, pending in another node, or not propagated.")
    raise SystemExit


try:
    receipt = w3.eth.get_transaction_receipt(TX_HASH)

    print("Receipt found.")
    print("Status:", receipt["status"])
    print("Block number:", receipt["blockNumber"])
    print("Gas used:", receipt["gasUsed"])

    if receipt["status"] == 1:
        print("Result: SUCCESS")
    else:
        print("Result: FAILED")

except TransactionNotFound:
    print("Receipt not found yet.")
    print("Result: PENDING or not mined yet.")
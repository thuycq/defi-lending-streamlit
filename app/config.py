import json
import os
from pathlib import Path

from dotenv import load_dotenv


# Project root:
# app/config.py -> app/ -> project root
PROJECT_ROOT = Path(__file__).resolve().parents[1]

ENV_PATH = PROJECT_ROOT / ".env"
CONTRACT_ADDRESSES_PATH = PROJECT_ROOT / "deployment" / "contract_addresses.json"
LENDING_POOL_ABI_PATH = PROJECT_ROOT / "deployment" / "abi" / "LendingPool.json"
MOCK_USD_ABI_PATH = PROJECT_ROOT / "deployment" / "abi" / "MockUSDToken.json"


def load_json(path: Path):
    """Load JSON file and return Python object."""
    if not path.exists():
        raise FileNotFoundError(f"File not found: {path}")

    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def load_abi(path: Path):
    """
    Load ABI file.

    Supports both formats:
    1. Raw ABI list:
       [...]
    2. Hardhat artifact format:
       {"abi": [...]}
    """
    data = load_json(path)

    if isinstance(data, list):
        return data

    if isinstance(data, dict) and "abi" in data:
        return data["abi"]

    raise ValueError(f"Invalid ABI format: {path}")


def get_config():
    """Load all app configuration needed for Streamlit/web3."""
    load_dotenv(ENV_PATH)

    rpc_url = os.getenv("SEPOLIA_RPC_URL")
    private_key = os.getenv("PRIVATE_KEY")

    if not rpc_url:
        raise ValueError(
            "Missing SEPOLIA_RPC_URL. Set it in .env for local development "
            "or in Streamlit Cloud Secrets for deployment."
        )

    addresses = load_json(CONTRACT_ADDRESSES_PATH)
    contracts = addresses.get("contracts", {})

    lending_pool_address = contracts.get("LendingPool")
    mock_usd_address = contracts.get("MockUSDToken")
    price_feed_address = contracts.get("ETH_USD_PriceFeed")

    if not lending_pool_address:
        raise ValueError("Missing LendingPool address in contract_addresses.json")

    if not mock_usd_address:
        raise ValueError("Missing MockUSDToken address in contract_addresses.json")

    if not price_feed_address:
        raise ValueError("Missing ETH_USD_PriceFeed address in contract_addresses.json")

    return {
        "network": addresses.get("network"),
        "chain_id": addresses.get("chainId"),
        "deployer": addresses.get("deployer"),
        "rpc_url": rpc_url,
        "lending_pool_address": lending_pool_address,
        "mock_usd_address": mock_usd_address,
        "price_feed_address": price_feed_address,
        "lending_pool_abi": load_abi(LENDING_POOL_ABI_PATH),
        "mock_usd_abi": load_abi(MOCK_USD_ABI_PATH),
        "private_key": private_key,
    }


if __name__ == "__main__":
    config = get_config()

    print("Config loaded successfully.")
    print("Network:", config["network"])
    print("Chain ID:", config["chain_id"])
    print("Deployer:", config["deployer"])
    print("LendingPool:", config["lending_pool_address"])
    print("MockUSDToken:", config["mock_usd_address"])
    print("ETH/USD Price Feed:", config["price_feed_address"])
    print("LendingPool ABI length:", len(config["lending_pool_abi"]))
    print("MockUSDToken ABI length:", len(config["mock_usd_abi"]))

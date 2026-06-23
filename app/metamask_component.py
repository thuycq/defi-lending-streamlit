import streamlit as st


METAMASK_HTML = """
<div class="wallet-box">
  <button id="connectBtn">Connect MetaMask</button>
  <div id="status" class="status">Wallet not connected</div>
</div>
"""


METAMASK_CSS = """
.wallet-box {
  border: 1px solid var(--st-border-color);
  border-radius: 0.75rem;
  padding: 1rem;
  background: var(--st-secondary-background-color);
  font-family: var(--st-font);
}

button {
  border: none;
  padding: 0.6rem 1rem;
  border-radius: var(--st-button-radius);
  background-color: var(--st-primary-color);
  color: white;
  font-weight: 600;
  cursor: pointer;
}

button:hover {
  opacity: 0.9;
}

.status {
  margin-top: 0.75rem;
  color: var(--st-text-color);
  font-size: 0.95rem;
  word-break: break-all;
}
"""


METAMASK_JS = """
export default function(component) {
  const { parentElement, setStateValue } = component;

  const connectBtn = parentElement.querySelector("#connectBtn");
  const statusDiv = parentElement.querySelector("#status");

  function shortAddress(address) {
    if (!address) return "";
    return address.slice(0, 6) + "..." + address.slice(-4);
  }

  function updateStatus(message) {
    statusDiv.textContent = message;
  }

  async function connectWallet() {
    if (!window.ethereum) {
      updateStatus("MetaMask is not installed.");
      setStateValue("status", "metamask_not_installed");
      setStateValue("wallet_address", "");
      setStateValue("chain_id", "");
      return;
    }

    try {
      const accounts = await window.ethereum.request({
        method: "eth_requestAccounts"
      });

      const chainId = await window.ethereum.request({
        method: "eth_chainId"
      });

      const account = accounts && accounts.length > 0 ? accounts[0] : "";

      if (!account) {
        updateStatus("No wallet account selected.");
        setStateValue("status", "no_account");
        setStateValue("wallet_address", "");
        setStateValue("chain_id", chainId || "");
        return;
      }

      updateStatus("Connected: " + shortAddress(account) + " | Chain: " + chainId);

      setStateValue("status", "connected");
      setStateValue("wallet_address", account);
      setStateValue("chain_id", chainId);
    } catch (error) {
      updateStatus("Connection rejected or failed: " + error.message);
      setStateValue("status", "error");
      setStateValue("wallet_address", "");
      setStateValue("chain_id", "");
    }
  }

  connectBtn.onclick = connectWallet;

  if (window.ethereum) {
    window.ethereum.on("accountsChanged", function(accounts) {
      const account = accounts && accounts.length > 0 ? accounts[0] : "";
      setStateValue("wallet_address", account);
      setStateValue("status", account ? "connected" : "disconnected");
      updateStatus(account ? "Connected: " + shortAddress(account) : "Wallet disconnected");
    });

    window.ethereum.on("chainChanged", function(chainId) {
      setStateValue("chain_id", chainId);
      updateStatus("Network changed. Chain: " + chainId);
    });
  }
}
"""


metamask_component = st.components.v2.component(
    name="metamask_connect",
    html=METAMASK_HTML,
    css=METAMASK_CSS,
    js=METAMASK_JS,
)


def render_metamask_connect():
    """Render MetaMask connect component and return wallet state."""
    result = metamask_component(
        default={
            "status": "not_connected",
            "wallet_address": "",
            "chain_id": "",
        },
        on_status_change=lambda: None,
        on_wallet_address_change=lambda: None,
        on_chain_id_change=lambda: None,
        key="metamask_connect_component",
    )

    return {
        "status": result.status,
        "wallet_address": result.wallet_address,
        "chain_id": result.chain_id,
    }

METAMASK_DEPOSIT_HTML = """
<div class="wallet-box">
  <label for="depositAmount">Deposit amount (ETH)</label>
  <input id="depositAmount" type="text" placeholder="Example: 0.00001" />
  <button id="depositBtn">Deposit with MetaMask</button>
  <div id="depositStatus" class="status">Ready to deposit with MetaMask.</div>
</div>
"""


METAMASK_DEPOSIT_CSS = """
.wallet-box {
  border: 1px solid var(--st-border-color);
  border-radius: 0.75rem;
  padding: 1rem;
  background: var(--st-secondary-background-color);
  font-family: var(--st-font);
}

label {
  display: block;
  margin-bottom: 0.4rem;
  font-weight: 600;
  color: var(--st-text-color);
}

input {
  width: 100%;
  box-sizing: border-box;
  padding: 0.55rem;
  margin-bottom: 0.75rem;
  border: 1px solid var(--st-border-color);
  border-radius: 0.5rem;
  background: var(--st-background-color);
  color: var(--st-text-color);
}

button {
  border: none;
  padding: 0.6rem 1rem;
  border-radius: var(--st-button-radius);
  background-color: var(--st-primary-color);
  color: white;
  font-weight: 600;
  cursor: pointer;
}

button:hover {
  opacity: 0.9;
}

button:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.status {
  margin-top: 0.75rem;
  color: var(--st-text-color);
  font-size: 0.95rem;
  word-break: break-all;
}
"""


METAMASK_DEPOSIT_JS = """
import { ethers } from "https://esm.sh/ethers@6.13.4";

export default function(component) {
  const { parentElement, setStateValue, data } = component;

  const amountInput = parentElement.querySelector("#depositAmount");
  const depositBtn = parentElement.querySelector("#depositBtn");
  const statusDiv = parentElement.querySelector("#depositStatus");

  function updateStatus(message) {
    statusDiv.textContent = message;
  }

  function isPositiveDecimal(value) {
    if (!value) return false;
    const cleaned = value.trim();
    if (!/^\\d*(\\.\\d+)?$/.test(cleaned)) return false;
    return Number(cleaned) > 0;
  }

  async function getCurrentAccount() {
    const accounts = await window.ethereum.request({
      method: "eth_accounts"
    });

    return accounts && accounts.length > 0 ? accounts[0] : "";
  }

  async function depositWithMetaMask() {
    const amountEth = amountInput.value.trim();

    if (!window.ethereum) {
      updateStatus("MetaMask is not installed.");
      setStateValue("deposit_status", "metamask_not_installed");
      setStateValue("deposit_error", "MetaMask is not installed.");
      return;
    }

    if (!data.wallet_address) {
      updateStatus("Please connect MetaMask first.");
      setStateValue("deposit_status", "wallet_not_connected");
      setStateValue("deposit_error", "Please connect MetaMask first.");
      return;
    }

    if (data.chain_id !== "0xaa36a7") {
      updateStatus("Please switch MetaMask to Sepolia.");
      setStateValue("deposit_status", "wrong_network");
      setStateValue("deposit_error", "Please switch MetaMask to Sepolia.");
      return;
    }

    if (!isPositiveDecimal(amountEth)) {
      updateStatus("Please enter a positive ETH amount.");
      setStateValue("deposit_status", "invalid_amount");
      setStateValue("deposit_error", "Please enter a positive ETH amount.");
      return;
    }

    try {
      depositBtn.disabled = true;
      updateStatus("Opening MetaMask confirmation...");

      const currentAccount = await getCurrentAccount();

      if (!currentAccount) {
        await window.ethereum.request({
          method: "eth_requestAccounts"
        });
      }

      const activeAccount = await getCurrentAccount();

      if (
        activeAccount.toLowerCase() !== data.wallet_address.toLowerCase()
      ) {
        throw new Error(
          "Connected account changed. Please reconnect MetaMask in the app."
        );
      }

      const provider = new ethers.BrowserProvider(window.ethereum);
      const signer = await provider.getSigner();
      const lendingPool = new ethers.Contract(
        data.lending_pool_address,
        data.lending_pool_abi,
        signer
      );

      const tx = await lendingPool.depositCollateral({
        value: ethers.parseEther(amountEth)
      });

      updateStatus("Transaction submitted: " + tx.hash);

      setStateValue("deposit_status", "submitted");
      setStateValue("deposit_tx_hash", tx.hash);
      setStateValue("deposit_error", "");
      setStateValue("deposit_amount_eth", amountEth);
    } catch (error) {
      updateStatus("Deposit failed: " + error.message);

      setStateValue("deposit_status", "error");
      setStateValue("deposit_error", error.message || "Deposit failed.");
    } finally {
      depositBtn.disabled = false;
    }
  }

  depositBtn.onclick = depositWithMetaMask;
}
"""


metamask_deposit_component = st.components.v2.component(
    name="metamask_deposit",
    html=METAMASK_DEPOSIT_HTML,
    css=METAMASK_DEPOSIT_CSS,
    js=METAMASK_DEPOSIT_JS,
)


def render_metamask_deposit(wallet_address: str, chain_id: str):
    """Render MetaMask deposit component and return transaction state."""
    try:
        from app.config import get_config
    except ModuleNotFoundError:
        from config import get_config

    config = get_config()

    result = metamask_deposit_component(
        data={
            "wallet_address": wallet_address,
            "chain_id": chain_id,
            "lending_pool_address": config["lending_pool_address"],
            "lending_pool_abi": config["lending_pool_abi"],
        },
        default={
            "deposit_status": "idle",
            "deposit_tx_hash": "",
            "deposit_error": "",
            "deposit_amount_eth": "",
        },
        on_deposit_status_change=lambda: None,
        on_deposit_tx_hash_change=lambda: None,
        on_deposit_error_change=lambda: None,
        on_deposit_amount_eth_change=lambda: None,
        key="metamask_deposit_component",
    )

    return {
        "deposit_status": result.deposit_status,
        "deposit_tx_hash": result.deposit_tx_hash,
        "deposit_error": result.deposit_error,
        "deposit_amount_eth": result.deposit_amount_eth,
    }

METAMASK_LENDING_ACTIONS_HTML = """
<div class="wallet-box">
  <div class="action-card">
    <h4>Borrow MockUSD</h4>
    <label for="borrowAmount">Borrow amount (MockUSD)</label>
    <input id="borrowAmount" type="text" placeholder="Example: 0.01" />
    <button id="borrowBtn">Borrow with MetaMask</button>
  </div>

  <div class="action-card">
    <h4>Repay MockUSD</h4>
    <label for="repayAmount">Repay amount (MockUSD)</label>
    <input id="repayAmount" type="text" placeholder="Example: 0.01" />
    <button id="repayBtn">Approve + Repay with MetaMask</button>
  </div>

  <div class="action-card">
    <h4>Withdraw Collateral</h4>
    <label for="withdrawAmount">Withdraw amount (ETH)</label>
    <input id="withdrawAmount" type="text" placeholder="Example: 0.00001" />
    <button id="withdrawBtn">Withdraw with MetaMask</button>
  </div>

  <div id="actionsStatus" class="status">Ready for MetaMask lending actions.</div>
</div>
"""


METAMASK_LENDING_ACTIONS_CSS = """
.wallet-box {
  border: 1px solid var(--st-border-color);
  border-radius: 0.75rem;
  padding: 1rem;
  background: var(--st-secondary-background-color);
  font-family: var(--st-font);
}

.action-card {
  border: 1px solid var(--st-border-color);
  border-radius: 0.75rem;
  padding: 1rem;
  margin-bottom: 1rem;
  background: var(--st-background-color);
}

h4 {
  margin-top: 0;
  margin-bottom: 0.75rem;
  color: var(--st-text-color);
}

label {
  display: block;
  margin-bottom: 0.4rem;
  font-weight: 600;
  color: var(--st-text-color);
}

input {
  width: 100%;
  box-sizing: border-box;
  padding: 0.55rem;
  margin-bottom: 0.75rem;
  border: 1px solid var(--st-border-color);
  border-radius: 0.5rem;
  background: var(--st-background-color);
  color: var(--st-text-color);
}

button {
  border: none;
  padding: 0.6rem 1rem;
  border-radius: var(--st-button-radius);
  background-color: var(--st-primary-color);
  color: white;
  font-weight: 600;
  cursor: pointer;
}

button:hover {
  opacity: 0.9;
}

button:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.status {
  margin-top: 0.75rem;
  color: var(--st-text-color);
  font-size: 0.95rem;
  word-break: break-all;
}
"""


METAMASK_LENDING_ACTIONS_JS = """
import { ethers } from "https://esm.sh/ethers@6.13.4";

export default function(component) {
  const { parentElement, setStateValue, data } = component;

  const borrowAmountInput = parentElement.querySelector("#borrowAmount");
  const repayAmountInput = parentElement.querySelector("#repayAmount");
  const withdrawAmountInput = parentElement.querySelector("#withdrawAmount");

  const borrowBtn = parentElement.querySelector("#borrowBtn");
  const repayBtn = parentElement.querySelector("#repayBtn");
  const withdrawBtn = parentElement.querySelector("#withdrawBtn");

  const statusDiv = parentElement.querySelector("#actionsStatus");

  function updateStatus(message) {
    statusDiv.textContent = message;
  }

  function isPositiveDecimal(value) {
    if (!value) return false;
    const cleaned = value.trim();
    if (!/^\\d*(\\.\\d+)?$/.test(cleaned)) return false;
    return Number(cleaned) > 0;
  }

  function setAllButtonsDisabled(disabled) {
    borrowBtn.disabled = disabled;
    repayBtn.disabled = disabled;
    withdrawBtn.disabled = disabled;
  }

  async function getCurrentAccount() {
    const accounts = await window.ethereum.request({
      method: "eth_accounts"
    });

    return accounts && accounts.length > 0 ? accounts[0] : "";
  }

  async function validateWallet() {
    if (!window.ethereum) {
      throw new Error("MetaMask is not installed.");
    }

    if (!data.wallet_address) {
      throw new Error("Please connect MetaMask first.");
    }

    if (data.chain_id !== "0xaa36a7") {
      throw new Error("Please switch MetaMask to Sepolia.");
    }

    const currentAccount = await getCurrentAccount();

    if (!currentAccount) {
      await window.ethereum.request({
        method: "eth_requestAccounts"
      });
    }

    const activeAccount = await getCurrentAccount();

    if (
      activeAccount.toLowerCase() !== data.wallet_address.toLowerCase()
    ) {
      throw new Error(
        "Connected account changed. Please reconnect MetaMask in the app."
      );
    }
  }

  async function getContracts() {
    const provider = new ethers.BrowserProvider(window.ethereum);
    const signer = await provider.getSigner();

    const lendingPool = new ethers.Contract(
      data.lending_pool_address,
      data.lending_pool_abi,
      signer
    );

    const mockUsd = new ethers.Contract(
      data.mock_usd_address,
      data.mock_usd_abi,
      signer
    );

    return {
      lendingPool,
      mockUsd
    };
  }

  function resetResult(actionName) {
    setStateValue("last_action", actionName);
    setStateValue("last_status", "pending");
    setStateValue("last_tx_hash", "");
    setStateValue("approve_tx_hash", "");
    setStateValue("last_error", "");
    setStateValue("last_amount", "");
  }

  async function borrowWithMetaMask() {
    const amount = borrowAmountInput.value.trim();

    resetResult("borrow");

    try {
      if (!isPositiveDecimal(amount)) {
        throw new Error("Please enter a positive MockUSD amount.");
      }

      setAllButtonsDisabled(true);
      await validateWallet();

      updateStatus("Opening MetaMask confirmation for Borrow...");

      const { lendingPool } = await getContracts();
      const amountWei = ethers.parseUnits(amount, 18);

      const tx = await lendingPool.borrow(amountWei);

      updateStatus("Borrow transaction submitted: " + tx.hash);

      setStateValue("last_action", "borrow");
      setStateValue("last_status", "submitted");
      setStateValue("last_tx_hash", tx.hash);
      setStateValue("last_amount", amount);
      setStateValue("last_error", "");
    } catch (error) {
      updateStatus("Borrow failed: " + error.message);

      setStateValue("last_action", "borrow");
      setStateValue("last_status", "error");
      setStateValue("last_error", error.message || "Borrow failed.");
    } finally {
      setAllButtonsDisabled(false);
    }
  }

  async function repayWithMetaMask() {
    const amount = repayAmountInput.value.trim();

    resetResult("repay");

    try {
      if (!isPositiveDecimal(amount)) {
        throw new Error("Please enter a positive MockUSD amount.");
      }

      setAllButtonsDisabled(true);
      await validateWallet();

      const { lendingPool, mockUsd } = await getContracts();
      const amountWei = ethers.parseUnits(amount, 18);

      updateStatus("Step 1/2: Opening MetaMask confirmation for MockUSD approve...");

      const approveTx = await mockUsd.approve(
        data.lending_pool_address,
        amountWei
      );

      updateStatus(
        "Approve submitted: " +
        approveTx.hash +
        ". Waiting for confirmation before repay..."
      );

      setStateValue("approve_tx_hash", approveTx.hash);

      await approveTx.wait();

      updateStatus("Step 2/2: Opening MetaMask confirmation for Repay...");

      const repayTx = await lendingPool.repay(amountWei);

      updateStatus("Repay transaction submitted: " + repayTx.hash);

      setStateValue("last_action", "repay");
      setStateValue("last_status", "submitted");
      setStateValue("last_tx_hash", repayTx.hash);
      setStateValue("last_amount", amount);
      setStateValue("last_error", "");
    } catch (error) {
      updateStatus("Repay failed: " + error.message);

      setStateValue("last_action", "repay");
      setStateValue("last_status", "error");
      setStateValue("last_error", error.message || "Repay failed.");
    } finally {
      setAllButtonsDisabled(false);
    }
  }

  async function withdrawWithMetaMask() {
    const amount = withdrawAmountInput.value.trim();

    resetResult("withdraw");

    try {
      if (!isPositiveDecimal(amount)) {
        throw new Error("Please enter a positive ETH amount.");
      }

      setAllButtonsDisabled(true);
      await validateWallet();

      updateStatus("Opening MetaMask confirmation for Withdraw...");

      const { lendingPool } = await getContracts();
      const amountWei = ethers.parseEther(amount);

      const tx = await lendingPool.withdrawCollateral(amountWei);

      updateStatus("Withdraw transaction submitted: " + tx.hash);

      setStateValue("last_action", "withdraw");
      setStateValue("last_status", "submitted");
      setStateValue("last_tx_hash", tx.hash);
      setStateValue("last_amount", amount);
      setStateValue("last_error", "");
    } catch (error) {
      updateStatus("Withdraw failed: " + error.message);

      setStateValue("last_action", "withdraw");
      setStateValue("last_status", "error");
      setStateValue("last_error", error.message || "Withdraw failed.");
    } finally {
      setAllButtonsDisabled(false);
    }
  }

  borrowBtn.onclick = borrowWithMetaMask;
  repayBtn.onclick = repayWithMetaMask;
  withdrawBtn.onclick = withdrawWithMetaMask;
}
"""


metamask_lending_actions_component = st.components.v2.component(
    name="metamask_lending_actions",
    html=METAMASK_LENDING_ACTIONS_HTML,
    css=METAMASK_LENDING_ACTIONS_CSS,
    js=METAMASK_LENDING_ACTIONS_JS,
)


def render_metamask_lending_actions(wallet_address: str, chain_id: str):
    """Render MetaMask Borrow/Repay/Withdraw component and return transaction state."""
    try:
        from app.config import get_config
    except ModuleNotFoundError:
        from config import get_config

    config = get_config()

    result = metamask_lending_actions_component(
        data={
            "wallet_address": wallet_address,
            "chain_id": chain_id,
            "lending_pool_address": config["lending_pool_address"],
            "lending_pool_abi": config["lending_pool_abi"],
            "mock_usd_address": config["mock_usd_address"],
            "mock_usd_abi": config["mock_usd_abi"],
        },
        default={
            "last_action": "",
            "last_status": "idle",
            "last_tx_hash": "",
            "approve_tx_hash": "",
            "last_error": "",
            "last_amount": "",
        },
        on_last_action_change=lambda: None,
        on_last_status_change=lambda: None,
        on_last_tx_hash_change=lambda: None,
        on_approve_tx_hash_change=lambda: None,
        on_last_error_change=lambda: None,
        on_last_amount_change=lambda: None,
        key="metamask_lending_actions_component",
    )

    return {
        "last_action": result.last_action,
        "last_status": result.last_status,
        "last_tx_hash": result.last_tx_hash,
        "approve_tx_hash": result.approve_tx_hash,
        "last_error": result.last_error,
        "last_amount": result.last_amount,
    }
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
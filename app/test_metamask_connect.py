import streamlit as st

from metamask_component import render_metamask_connect


st.set_page_config(
    page_title="MetaMask Connect Test",
    page_icon="🦊",
    layout="centered",
)

st.title("MetaMask Connect Test")
st.write("Bước này chỉ test kết nối ví. Chưa gửi transaction.")

wallet = render_metamask_connect()

st.subheader("Wallet state from browser")
st.write(wallet)

if wallet["wallet_address"]:
    st.success(f"Connected wallet: {wallet['wallet_address']}")

    if wallet["chain_id"] == "0xaa36a7":
        st.success("Network: Sepolia")
    else:
        st.warning(
            f"Current chain_id = {wallet['chain_id']}. "
            "Please switch MetaMask to Sepolia."
        )
else:
    st.info("Click Connect MetaMask to start.")
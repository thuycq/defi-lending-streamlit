from decimal import Decimal, InvalidOperation
import time
import streamlit as st

try:
    from app.blockchain import (
        read_basic_status,
        read_user_position,
        get_loan_status_label,
        format_decimal,
        deposit_collateral,
        borrow_mock_usd,
        repay_mock_usd,
        withdraw_collateral,
    )
    from app.metamask_component import render_metamask_connect
except ModuleNotFoundError:
    from blockchain import (
        read_basic_status,
        read_user_position,
        get_loan_status_label,
        format_decimal,
        deposit_collateral,
        borrow_mock_usd,
        repay_mock_usd,
        withdraw_collateral,
    )
    from metamask_component import render_metamask_connect

SEPOLIA_ETHERSCAN_BASE = "https://sepolia.etherscan.io"


def etherscan_address_url(address):
    return f"{SEPOLIA_ETHERSCAN_BASE}/address/{address}"


def etherscan_tx_url(tx_hash):
    return f"{SEPOLIA_ETHERSCAN_BASE}/tx/{tx_hash}"

def parse_positive_decimal(value, field_name):
    """
    Parse user input into a positive Decimal.

    Returns:
    - Decimal value if valid
    - None if invalid, and shows Streamlit warning
    """
    try:
        parsed_value = Decimal(str(value).strip())

        if parsed_value <= 0:
            st.warning(f"{field_name} phải lớn hơn 0.")
            return None

        return parsed_value

    except InvalidOperation:
        st.warning(f"{field_name} không hợp lệ. Vui lòng nhập số, ví dụ 0.0001 hoặc 0.1.")
        return None

def save_last_transaction(action, tx_hash, status=None):
    """Save latest transaction info to Streamlit session state."""
    st.session_state["last_transaction"] = {
        "action": action,
        "tx_hash": tx_hash,
        "status": status,
    }


def rerun_after_success(seconds=2):
    """Wait briefly, then rerun app to reload on-chain data."""
    time.sleep(seconds)
    st.rerun()


st.set_page_config(
    page_title="DeFi Lending Demo",
    page_icon="💸",
    layout="wide",
)


st.title("DeFi Lending Demo")
st.caption("Streamlit local dashboard đọc dữ liệu thật từ Ethereum Sepolia testnet")

if "last_transaction" in st.session_state:
    last_tx = st.session_state["last_transaction"]

    st.success(
        f"Giao dịch gần nhất: {last_tx['action']} | Status: {last_tx['status']}"
    )

    st.markdown(
        f"[Xem transaction trên Sepolia Etherscan]({etherscan_tx_url(last_tx['tx_hash'])})"
    )

with st.sidebar:
    st.header("Thông tin demo")
    st.write("Network: Ethereum Sepolia")
    st.write("Oracle: Chainlink ETH/USD Price Feed")
    st.write("Token vay: MockUSD")
    st.warning("Demo dùng testnet, không dùng tiền thật.")

    st.divider()
    st.header("Kết nối ví")
    wallet_state = render_metamask_connect()

    metamask_wallet = wallet_state.get("wallet_address", "")
    metamask_chain_id = wallet_state.get("chain_id", "")
    metamask_connected = (
        wallet_state.get("status") == "connected"
        and bool(metamask_wallet)
    )
    metamask_on_sepolia = metamask_chain_id == "0xaa36a7"

    if metamask_connected and metamask_on_sepolia:
        st.success("MetaMask đã kết nối Sepolia.")
    elif metamask_connected and not metamask_on_sepolia:
        st.warning(
            f"MetaMask đang ở chain_id = {metamask_chain_id}. "
            "Vui lòng chuyển sang Sepolia."
        )
    else:
        st.info("Có thể kết nối MetaMask để đọc trạng thái ví của người dùng.")


try:
    status = read_basic_status()

    with st.sidebar:
        st.divider()
        st.header("Wallet cần đọc")

        default_wallet = status["deployer"]

        if metamask_connected and metamask_on_sepolia:
            default_wallet = metamask_wallet
            st.caption("Dashboard đang đọc ví MetaMask đã kết nối.")
        else:
            st.caption("Chưa kết nối MetaMask Sepolia. Dashboard đang đọc ví demo mặc định.")

        wallet_input = st.text_input(
            "Wallet address",
            value=default_wallet,
            help=(
                "Nếu MetaMask đã kết nối Sepolia, ô này sẽ dùng ví MetaMask. "
                "Bạn vẫn có thể nhập ví khác để xem trạng thái read-only."
            ),
        )

        refresh = st.button("Refresh data")

    position = read_user_position(wallet_input)

    loan_status = get_loan_status_label(
        position["health_factor"],
        position["debt_mock_usd"],
    )

    st.subheader("1. Kết nối blockchain")

    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric("RPC connected", "Yes" if status["is_connected"] else "No")

    with col2:
        st.metric("Chain ID", status["chain_id"])

    with col3:
        st.metric("Latest block", status["latest_block"])

    st.divider()

    st.subheader("2. Market data")

    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric(
            "ETH/USD Price",
            f"{format_decimal(status['eth_price']['price'], 2)} USD",
        )

    with col2:
        st.metric(
            "Oracle decimals",
            status["eth_price"]["decimals"],
        )

    with col3:
        st.metric(
            "Updated at",
            status["eth_price"]["updated_at"],
        )

    with st.expander("Xem địa chỉ contract"):
        st.markdown(
            f"[LendingPool]({etherscan_address_url(status['lending_pool_address'])})"
        )
        st.code(status["lending_pool_address"])

        st.markdown(
            f"[MockUSDToken]({etherscan_address_url(status['mock_usd_address'])})"
        )
        st.code(status["mock_usd_address"])

        st.markdown(
            f"[ETH/USD Price Feed]({etherscan_address_url(status['price_feed_address'])})"
    )
        st.code(status["price_feed_address"])

    st.divider()

    st.subheader("3. Wallet dashboard")

    st.markdown(
    f"Wallet: [{position['user_address']}]({etherscan_address_url(position['user_address'])})"
    )

    col1, col2 = st.columns(2)

    with col1:
        st.metric(
            "Wallet ETH balance",
            f"{format_decimal(position['eth_balance'], 6)} ETH",
        )

    with col2:
        st.metric(
            "Wallet MockUSD balance",
            f"{format_decimal(position['mock_usd_balance'], 6)} MockUSD",
        )

    st.divider()

    st.subheader("4. Lending position")

    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric(
            "Collateral ETH",
            f"{format_decimal(position['collateral_eth'], 6)} ETH",
        )

    with col2:
        st.metric(
            "Debt MockUSD",
            f"{format_decimal(position['debt_mock_usd'], 6)} MockUSD",
        )

    with col3:
        st.metric(
            "Loan status",
            loan_status,
        )

    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric(
            "Collateral value",
            f"{format_decimal(position['collateral_value_usd'], 4)} USD",
        )

    with col2:
        st.metric(
            "Max borrowable",
            f"{format_decimal(position['max_borrowable_usd'], 4)} MockUSD",
        )

    with col3:
        st.metric(
            "Current LTV",
            f"{format_decimal(position['current_ltv_percent'], 2)} %",
        )

    st.metric(
        "Health Factor",
        format_decimal(position["health_factor"], 4),
    )

    if loan_status == "Safe":
        st.success("Khoản vay đang an toàn vì Health Factor cao hơn 1.")
    elif loan_status == "Warning":
        st.warning("Khoản vay cần theo dõi vì Health Factor gần ngưỡng thanh lý.")
    elif loan_status == "Liquidatable":
        st.error("Khoản vay có thể bị thanh lý vì Health Factor dưới 1.")
    else:
        st.info("Ví hiện chưa có dư nợ.")

    st.divider()
    st.info(
        "Nhánh MetaMask integration hiện đang ở chế độ read-only. "
        "Các nút giao dịch backend-signer cũ được tạm ẩn để tránh nhầm lẫn. "
        "Bước tiếp theo sẽ thêm Deposit/Borrow/Repay/Withdraw do MetaMask ký trực tiếp."
    )
    st.stop()

    st.divider()
    st.subheader("5. Deposit collateral")

    st.write(
        """
        Chức năng này gửi giao dịch thật lên Sepolia testnet.
        ETH dùng ở đây là Sepolia ETH, không phải ETH thật.
        """
    )

    with st.form("deposit_form"):
        deposit_amount = st.text_input(
            "Số ETH muốn nạp làm collateral",
            value="0.0001",
            help="Nên test số nhỏ, ví dụ 0.0001 ETH.",
        )

        confirm_deposit = st.checkbox(
            "Tôi xác nhận đây là giao dịch testnet và đồng ý gửi transaction.",
        )

        submitted_deposit = st.form_submit_button("Deposit collateral")

        if submitted_deposit:
            if not confirm_deposit:
                st.warning("Cần tick xác nhận trước khi gửi giao dịch.")
            else:
                try:
                    with st.spinner("Đang gửi giao dịch deposit lên Sepolia..."):
                        receipt = deposit_collateral(deposit_amount)

                    if receipt["status"] == 1:
                        st.success("Deposit collateral thành công.")
                        save_last_transaction(
                            "Deposit collateral",
                            receipt["tx_hash"],
                            receipt["status"],
                        )
                        rerun_after_success()
                    elif receipt["status"] == 0:
                        st.error("Transaction đã gửi nhưng bị fail.")
                    elif receipt.get("is_pending"):
                        st.warning(
                            "Transaction đã được gửi lên Sepolia nhưng chưa lấy được receipt. "
                            "Vui lòng chờ một chút rồi bấm Refresh data hoặc kiểm tra trên Etherscan."
                        )
                    else:
                        st.warning("Transaction đã gửi nhưng chưa xác định được trạng thái.")

                    st.write("Transaction hash:")
                    st.code(receipt["tx_hash"])

                    st.markdown(
                        f"[Xem transaction trên Sepolia Etherscan]({etherscan_tx_url(receipt['tx_hash'])})"
                    )

                    if receipt["block_number"] is not None:
                        st.write("Block number:", receipt["block_number"])

                    if receipt["gas_used"] is not None:
                        st.write("Gas used:", receipt["gas_used"])

                    st.info("Bấm Rerun hoặc Refresh data để cập nhật lại dashboard.")

                except Exception as tx_error:
                    st.error("Lỗi khi gửi giao dịch deposit.")
                    st.exception(tx_error)

    st.divider()

    st.subheader("6. Borrow MockUSD")

    available_to_borrow = position["max_borrowable_usd"] - position["debt_mock_usd"]

    if available_to_borrow < 0:
        available_to_borrow = 0

    st.write(
        """
        Chức năng này gửi giao dịch vay MockUSD lên Sepolia testnet.
        MockUSD là token giả lập, được mint khi người dùng vay theo hạn mức collateral.
        """
    )

    st.info(
        f"Số MockUSD còn có thể vay thêm ước tính: "
        f"{format_decimal(available_to_borrow, 6)} MockUSD"
    )

    with st.form("borrow_form"):
        borrow_amount = st.text_input(
            "Số MockUSD muốn vay thêm",
            value="0.1",
            help="Nên test số nhỏ, ví dụ 0.1 MockUSD.",
        )

        confirm_borrow = st.checkbox(
            "Tôi xác nhận đây là giao dịch testnet và đồng ý vay MockUSD.",
        )

        submitted_borrow = st.form_submit_button("Borrow MockUSD")

        if submitted_borrow:
            borrow_amount_decimal = parse_positive_decimal(
                borrow_amount,
                "Số MockUSD muốn vay",
            )

            if borrow_amount_decimal is None:
                st.stop()

            if borrow_amount_decimal > available_to_borrow:
                st.warning(
                    f"Số vay vượt hạn mức còn lại. "
                    f"Tối đa hiện có thể vay thêm là {format_decimal(available_to_borrow, 6)} MockUSD."
                )
                st.stop()

            if not confirm_borrow:
                st.warning("Cần tick xác nhận trước khi gửi giao dịch.")
            else:
                try:
                    with st.spinner("Đang gửi giao dịch borrow lên Sepolia..."):
                        receipt = borrow_mock_usd(borrow_amount)

                    if receipt["status"] == 1:
                        st.success("Borrow MockUSD thành công.")
                        save_last_transaction(
                            "Borrow MockUSD",
                            receipt["tx_hash"],
                            receipt["status"],
                        )
                        rerun_after_success()
                    elif receipt["status"] == 0:
                        st.error("Transaction đã gửi nhưng bị fail.")
                    elif receipt.get("is_pending"):
                        st.warning(
                            "Transaction đã được gửi lên Sepolia nhưng chưa lấy được receipt. "
                            "Vui lòng chờ một chút rồi bấm Refresh data hoặc kiểm tra trên Etherscan."
                        )
                    else:
                        st.warning("Transaction đã gửi nhưng chưa xác định được trạng thái.")

                    st.write("Transaction hash:")
                    st.code(receipt["tx_hash"])

                    st.markdown(
                        f"[Xem transaction trên Sepolia Etherscan]({etherscan_tx_url(receipt['tx_hash'])})"
                    )

                    if receipt["block_number"] is not None:
                        st.write("Block number:", receipt["block_number"])

                    if receipt["gas_used"] is not None:
                        st.write("Gas used:", receipt["gas_used"])

                    st.info("Bấm Rerun hoặc Refresh data để cập nhật lại dashboard.")

                except Exception as tx_error:
                    st.error("Lỗi khi gửi giao dịch borrow.")
                    st.exception(tx_error)

    st.divider()

    st.subheader("7. Repay MockUSD")

    st.write(
        """
        Chức năng này dùng MockUSD trong ví để trả nợ.
        Vì MockUSD là ERC-20 token, hệ thống sẽ gửi 2 giao dịch:
        approve MockUSD trước, sau đó mới gọi repay.
        """
    )

    st.info(
        f"Dư nợ hiện tại: {format_decimal(position['debt_mock_usd'], 6)} MockUSD"
    )

    st.info(
        f"Số dư MockUSD trong ví: {format_decimal(position['mock_usd_balance'], 6)} MockUSD"
    )

    with st.form("repay_form"):
        repay_amount = st.text_input(
            "Số MockUSD muốn trả",
            value="0.1",
            help="Nên test số nhỏ, ví dụ 0.1 MockUSD.",
        )

        confirm_repay = st.checkbox(
            "Tôi xác nhận đây là giao dịch testnet và đồng ý trả nợ MockUSD.",
        )

        submitted_repay = st.form_submit_button("Repay MockUSD")

        if submitted_repay:
            repay_amount_decimal = parse_positive_decimal(
                repay_amount,
                "Số MockUSD muốn trả",
            )

            if repay_amount_decimal is None:
                st.stop()

            if repay_amount_decimal > position["debt_mock_usd"]:
                st.warning(
                    f"Số trả nợ vượt dư nợ hiện tại. "
                    f"Dư nợ hiện tại là {format_decimal(position['debt_mock_usd'], 6)} MockUSD."
                )
                st.stop()

            if repay_amount_decimal > position["mock_usd_balance"]:
                st.warning(
                    f"Số trả nợ vượt số dư MockUSD trong ví. "
                    f"Số dư hiện tại là {format_decimal(position['mock_usd_balance'], 6)} MockUSD."
                )
                st.stop()

            if not confirm_repay:
                st.warning("Cần tick xác nhận trước khi gửi giao dịch.")
            else:
                try:
                    with st.spinner("Đang gửi approve + repay lên Sepolia..."):
                        result = repay_mock_usd(repay_amount)

                    st.write("Approve transaction:")
                    st.code(result["approve"]["tx_hash"])

                    st.markdown(
                        f"[Xem approve transaction trên Sepolia Etherscan]({etherscan_tx_url(result['approve']['tx_hash'])})"
                    )

                    if result["approve"]["status"] == 1:
                        st.success("Approve MockUSD thành công.")
                    elif result["approve"]["status"] == 0:
                        st.error("Approve transaction bị fail.")
                    elif result["approve"].get("is_pending"):
                        st.warning(
                            "Approve transaction đã gửi nhưng chưa lấy được receipt. "
                            "Vui lòng kiểm tra trên Etherscan."
                        )
                    else:
                        st.warning("Approve transaction chưa xác định được trạng thái.")

                    if result["repay"] is not None:
                        st.write("Repay transaction:")
                        st.code(result["repay"]["tx_hash"])

                        st.markdown(
                            f"[Xem repay transaction trên Sepolia Etherscan]({etherscan_tx_url(result['repay']['tx_hash'])})"
                        )

                        if result["repay"]["status"] == 1:
                            st.success("Repay MockUSD thành công.")
                            save_last_transaction(
                                "Repay MockUSD",
                                result["repay"]["tx_hash"],
                                result["repay"]["status"],
                            )
                            rerun_after_success()
                        elif result["repay"]["status"] == 0:
                            st.error("Repay transaction bị fail.")
                        elif result["repay"].get("is_pending"):
                            st.warning(
                                "Repay transaction đã gửi nhưng chưa lấy được receipt. "
                                "Vui lòng chờ một chút rồi bấm Refresh data hoặc kiểm tra trên Etherscan."
                            )
                        else:
                            st.warning("Repay transaction chưa xác định được trạng thái.")

                        if result["repay"]["block_number"] is not None:
                            st.write("Repay block number:", result["repay"]["block_number"])

                        if result["repay"]["gas_used"] is not None:
                            st.write("Repay gas used:", result["repay"]["gas_used"])

                    else:
                        st.warning(
                            "Chưa gửi repay transaction vì approve chưa được xác nhận thành công."
                        )

                    st.info("Bấm Rerun hoặc Refresh data để cập nhật lại dashboard.")

                except Exception as tx_error:
                    st.error("Lỗi khi gửi giao dịch repay.")
                    st.exception(tx_error)

    st.divider()

    st.subheader("8. Withdraw collateral")

    st.write(
        """
        Chức năng này rút ETH collateral khỏi LendingPool.
        Contract chỉ cho rút nếu khoản vay sau khi rút vẫn an toàn.
        """
    )

    st.info(
        f"Collateral hiện tại: {format_decimal(position['collateral_eth'], 6)} ETH"
    )

    st.info(
        f"Health Factor hiện tại: {format_decimal(position['health_factor'], 4)}"
    )

    with st.form("withdraw_form"):
        withdraw_amount = st.text_input(
            "Số ETH collateral muốn rút",
            value="0.0001",
            help="Nên test số nhỏ, ví dụ 0.0001 ETH.",
        )

        confirm_withdraw = st.checkbox(
            "Tôi xác nhận đây là giao dịch testnet và đồng ý rút collateral.",
        )

        submitted_withdraw = st.form_submit_button("Withdraw collateral")

        if submitted_withdraw:
            withdraw_amount_decimal = parse_positive_decimal(
                withdraw_amount,
                "Số ETH collateral muốn rút",
            )

            if withdraw_amount_decimal is None:
                st.stop()

            if withdraw_amount_decimal > position["collateral_eth"]:
                st.warning(
                    f"Số rút vượt collateral hiện tại. "
                    f"Collateral hiện tại là {format_decimal(position['collateral_eth'], 6)} ETH."
                )
                st.stop()

            if not confirm_withdraw:
                st.warning("Cần tick xác nhận trước khi gửi giao dịch.")
            else:
                try:
                    with st.spinner("Đang gửi giao dịch withdraw lên Sepolia..."):
                        receipt = withdraw_collateral(withdraw_amount)

                    if receipt["status"] == 1:
                        st.success("Withdraw collateral thành công.")
                        save_last_transaction(
                            "Withdraw collateral",
                            receipt["tx_hash"],
                            receipt["status"],
                        )
                        rerun_after_success()
                    elif receipt["status"] == 0:
                        st.error("Transaction đã gửi nhưng bị fail.")
                    elif receipt.get("is_pending"):
                        st.warning(
                            "Transaction đã được gửi lên Sepolia nhưng chưa lấy được receipt. "
                            "Vui lòng chờ một chút rồi bấm Refresh data hoặc kiểm tra trên Etherscan."
                        )
                    else:
                        st.warning("Transaction đã gửi nhưng chưa xác định được trạng thái.")

                    st.write("Transaction hash:")
                    st.code(receipt["tx_hash"])

                    st.markdown(
                        f"[Xem transaction trên Sepolia Etherscan]({etherscan_tx_url(receipt['tx_hash'])})"
                    )

                    if receipt["block_number"] is not None:
                        st.write("Block number:", receipt["block_number"])

                    if receipt["gas_used"] is not None:
                        st.write("Gas used:", receipt["gas_used"])

                    st.info("Bấm Rerun hoặc Refresh data để cập nhật lại dashboard.")

                except Exception as tx_error:
                    st.error("Lỗi khi gửi giao dịch withdraw.")
                    st.exception(tx_error)

    st.divider()

    st.subheader("9. Ghi chú demo")

    st.write(
        """
        Dashboard này đang đọc trực tiếp dữ liệu từ Sepolia thông qua "deployer": config["deployer"],QuickNode RPC.
        Giá ETH/USD được lấy từ Chainlink Price Feed thông qua LendingPool smart contract.
        Các thao tác ghi giao dịch như deposit, borrow, repay và withdraw sẽ được thêm ở bước sau.
        """
    )

except Exception as e:
    st.error("Dashboard lỗi khi đọc dữ liệu từ Sepolia.")
    st.exception(e)
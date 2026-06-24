import streamlit as st
import pandas as pd
import os
import sys
import json
import time

# Thêm thư mục hiện tại vào python path để import module app
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Load dotenv thủ công
try:
    from dotenv import load_dotenv
    dotenv_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "app", ".env")
    if os.path.exists(dotenv_path):
        load_dotenv(dotenv_path)
    else:
        load_dotenv()
except:
    pass

from app.tools import get_portfolio, add_to_portfolio, remove_from_portfolio, get_stock_quote, run_market_scan
from app.agent import root_agent
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types

# Translation Dictionary
TRANSLATIONS = {
    "English": {
        "page_title": "💰 Personal Wealth Concierge & Sentinel Dashboard",
        "title": "💰 Personal Wealth Concierge & Sentinel Dashboard",
        "portfolio_header": "📊 Personal Portfolio",
        "total_cost": "Total Cost Value",
        "total_market": "Total Market Value",
        "total_pl": "Total Unrealized P&L",
        "empty_portfolio": "Your portfolio is currently empty. Add stocks using the form below.",
        "portfolio_structure": "📈 **Portfolio Structure by Market Value**",
        "sentinel_header": "⏰ Sentinel System (Monitoring & Email Alerts)",
        "sentinel_info": "Sentinel system is running in the background every 10 minutes to send automated email alerts.",
        "manual_scan_btn": "🔔 Trigger Manual Scan Now",
        "scanning": "Connecting to Vnstock and analyzing portfolio...",
        "update_portfolio_header": "⚙️ **Quick Portfolio Update:**",
        "stock_code": "Stock Symbol (e.g. FPT)",
        "quantity": "Quantity",
        "cost_basis": "Cost Basis (k VND)",
        "alert_thresh": "Alert Threshold (%)",
        "action": "Action",
        "add_update": "Add/Update",
        "delete": "Delete",
        "confirm_btn": "Confirm Execution",
        "enter_symbol": "Please enter a stock symbol.",
        "chatbot_header": "💬 Personal Wealth Concierge",
        "welcome_msg": "Hello Mr.Híu! I am your **Personal Wealth Concierge & Sentinel**. I can help you manage your portfolio, analyze stock quotes and news, and trigger volatility scan alerts. How can I assist you today?",
        "chat_placeholder": "Type your request (e.g., 'Add stock VCB to portfolio', or 'Analyze symbol FPT')",
        "thinking": "Concierge is thinking and analyzing...",
        "error_agent": "An error occurred while communicating with the Agent: ",
        "no_response": "Sorry, I did not receive a response from the system.",
        "headers": {
            "Mã CK": "Symbol",
            "Số lượng": "Quantity",
            "Giá vốn (k VNĐ)": "Cost Basis (k VND)",
            "Giá hiện tại (k VNĐ)": "Current Price (k VND)",
            "Giá trị vốn (k VNĐ)": "Cost Value (k VND)",
            "Giá trị thị trường (k VNĐ)": "Market Value (k VND)",
            "Lãi/Lỗ (k VNĐ)": "P&L (k VND)",
            "Lãi/Lỗ (%)": "P&L (%)",
            "Ngưỡng cảnh báo (%)": "Alert Threshold (%)"
        }
    },
    "Tiếng Việt": {
        "page_title": "💰 Personal Wealth Concierge & Sentinel Dashboard",
        "title": "💰 Personal Wealth Concierge & Sentinel Dashboard",
        "portfolio_header": "📊 Danh mục tài sản cá nhân",
        "total_cost": "Tổng giá trị vốn",
        "total_market": "Tổng giá trị thị trường",
        "total_pl": "Tổng Lãi/Lỗ chưa thực hiện",
        "empty_portfolio": "Danh mục đầu tư hiện đang trống. Hãy thêm cổ phiếu ở bảng điều khiển bên dưới.",
        "portfolio_structure": "📈 **Cơ cấu danh mục theo Giá trị thị trường**",
        "sentinel_header": "⏰ Hệ thống Sentinel (Giám sát & Email Cảnh báo)",
        "sentinel_info": "Hệ thống Sentinel đang chạy ngầm định kỳ 10 phút một lần để gửi email tự động.",
        "manual_scan_btn": "🔔 Kích hoạt quét thủ công ngay lập tức",
        "scanning": "Đang kết nối Vnstock và đối chiếu danh mục...",
        "update_portfolio_header": "⚙️ **Cập nhật nhanh danh mục:**",
        "stock_code": "Mã cổ phiếu (ví dụ: FPT)",
        "quantity": "Số lượng",
        "cost_basis": "Giá vốn (k VNĐ)",
        "alert_thresh": "Ngưỡng cảnh báo (%)",
        "action": "Hành động",
        "add_update": "Thêm/Cập nhật",
        "delete": "Xóa",
        "confirm_btn": "Xác nhận thực hiện",
        "enter_symbol": "Vui lòng nhập mã cổ phiếu.",
        "chatbot_header": "💬 Trợ lý Tài chính Cá nhân",
        "welcome_msg": "Xin chào Mr.Híu! Tôi là **Trợ lý Tài chính Cá nhân & Sentinel**. Tôi có thể giúp anh quản lý danh mục tài sản, kiểm tra giá, tin tức thị trường và kích hoạt quét cảnh báo biến động. Anh cần tôi hỗ trợ gì hôm nay?",
        "chat_placeholder": "Nhập yêu cầu (ví dụ: 'Thêm mã VCB vào danh mục', hoặc 'Phân tích mã FPT')",
        "thinking": "Trợ lý đang suy nghĩ và tổng hợp thông tin...",
        "error_agent": "Đã xảy ra lỗi khi trao đổi với Agent: ",
        "no_response": "Xin lỗi, tôi không nhận được phản hồi từ hệ thống.",
        "headers": {
            "Mã CK": "Mã CK",
            "Số lượng": "Số lượng",
            "Giá vốn (k VNĐ)": "Giá vốn (k VNĐ)",
            "Giá hiện tại (k VNĐ)": "Giá hiện tại (k VNĐ)",
            "Giá trị vốn (k VNĐ)": "Giá trị vốn (k VNĐ)",
            "Giá trị thị trường (k VNĐ)": "Giá trị thị trường (k VNĐ)",
            "Lãi/Lỗ (k VNĐ)": "Lãi/Lỗ (k VNĐ)",
            "Lãi/Lỗ (%)": "Lãi/Lỗ (%)",
            "Ngưỡng cảnh báo (%)": "Ngưỡng cảnh báo (%)"
        }
    }
}

# Sidebar Language Selection
st.sidebar.title("⚙️ Settings / Cấu hình")
lang = st.sidebar.selectbox("Language / Ngôn ngữ", ["English", "Tiếng Việt"], index=0)
t = TRANSLATIONS[lang]

# Cấu hình Page
st.set_page_config(
    page_title=t["page_title"],
    page_icon="💰",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Dark Mode Custom CSS
st.markdown("""
<style>
    .metric-card {
        background-color: #1e1e1e;
        border: 1px solid #333;
        padding: 15px;
        border-radius: 8px;
        text-align: center;
    }
    .metric-value {
        font-size: 22px;
        font-weight: bold;
    }
    .green-text { color: #00cc66; }
    .red-text { color: #ff3333; }
</style>
""", unsafe_allow_html=True)

# Khởi tạo hoặc cập nhật trạng thái khi chuyển ngôn ngữ
if "current_lang" not in st.session_state:
    st.session_state.current_lang = lang

if "runner" not in st.session_state or st.session_state.runner.agent.model != root_agent.model or st.session_state.current_lang != lang:
    st.session_state.current_lang = lang
    session_service = InMemorySessionService()
    st.session_state.session_service = session_service
    st.session_state.runner = Runner(agent=root_agent, session_service=session_service, app_name="app")
    st.session_state.session = session_service.create_session_sync(user_id="default_user", app_name="app")
    st.session_state.chat_history = []

# Title
st.title(t["title"])
st.markdown("---")

# Hàm load danh mục mở rộng (tính thêm giá trị thị trường và lãi/lỗ)
def load_portfolio_details():
    res = get_portfolio()
    if res["status"] != "success":
        return []
    
    portfolio = res["portfolio"]
    detailed_portfolio = []
    
    for item in portfolio:
        symbol = item["symbol"]
        volume = item["volume"]
        cost_basis = item["cost_basis"] # nghìn VNĐ
        alert_threshold = item["alert_threshold"]
        
        # Lấy giá trực tuyến
        quote_res = get_stock_quote(symbol)
        current_price = cost_basis # fallback
        if quote_res["status"] == "success":
            # close_price từ API dạng VNĐ, chuyển sang nghìn VNĐ
            current_price = float(quote_res["quote"].get("close_price", 0)) / 1000.0
            
        total_cost = cost_basis * volume
        market_value = current_price * volume
        profit_loss = market_value - total_cost
        profit_loss_pct = (profit_loss / total_cost * 100.0) if total_cost > 0 else 0
        
        detailed_portfolio.append({
            "Mã CK": symbol,
            "Số lượng": volume,
            "Giá vốn (k VNĐ)": cost_basis,
            "Giá hiện tại (k VNĐ)": current_price,
            "Giá trị vốn (k VNĐ)": total_cost,
            "Giá trị thị trường (k VNĐ)": market_value,
            "Lãi/Lỗ (k VNĐ)": profit_loss,
            "Lãi/Lỗ (%)": profit_loss_pct,
            "Ngưỡng cảnh báo (%)": alert_threshold
        })
    return detailed_portfolio

# Khởi tạo hoặc làm mới danh mục
detailed_portfolio = load_portfolio_details()
df_portfolio = pd.DataFrame(detailed_portfolio)

# Layout chính: 2 cột (Cột 1: Danh mục & Quét Sentinel; Cột 2: Trợ lý Chatbot)
col1, col2 = st.columns([3, 2])

with col1:
    st.subheader(t["portfolio_header"])
    
    if not df_portfolio.empty:
        # Hiển thị các chỉ số tổng quan ở hàng trên
        total_cost_val = df_portfolio["Giá trị vốn (k VNĐ)"].sum()
        total_market_val = df_portfolio["Giá trị thị trường (k VNĐ)"].sum()
        total_pl = total_market_val - total_cost_val
        total_pl_pct = (total_pl / total_cost_val * 100.0) if total_cost_val > 0 else 0
        
        pl_color = "green-text" if total_pl >= 0 else "red-text"
        pl_sign = "+" if total_pl >= 0 else ""
        
        m_col1, m_col2, m_col3 = st.columns(3)
        with m_col1:
            st.markdown(f"""
            <div class="metric-card">
                <div style='color: #888;'>{t["total_cost"]}</div>
                <div class="metric-value">{total_cost_val:,.2f} k VNĐ</div>
            </div>
            """, unsafe_allow_html=True)
        with m_col2:
            st.markdown(f"""
            <div class="metric-card">
                <div style='color: #888;'>{t["total_market"]}</div>
                <div class="metric-value">{total_market_val:,.2f} k VNĐ</div>
            </div>
            """, unsafe_allow_html=True)
        with m_col3:
            st.markdown(f"""
            <div class="metric-card">
                <div style='color: #888;'>{t["total_pl"]}</div>
                <div class="metric-value {pl_color}">{pl_sign}{total_pl:,.2f} k VNĐ ({pl_sign}{total_pl_pct:.2f}%)</div>
            </div>
            """, unsafe_allow_html=True)
            
        st.markdown("<br>", unsafe_allow_html=True)
        
        # Bảng danh mục đã chuyển đổi Header cột
        def highlight_pl(val):
            color = '#00cc66' if val >= 0 else '#ff3333'
            return f'color: {color}; font-weight: bold'
        
        df_display = df_portfolio.rename(columns=t["headers"])
        
        st.dataframe(
            df_display.style.format({
                t["headers"]["Giá vốn (k VNĐ)"]: "{:,.2f}",
                t["headers"]["Giá hiện tại (k VNĐ)"]: "{:,.2f}",
                t["headers"]["Giá trị vốn (k VNĐ)"]: "{:,.2f}",
                t["headers"]["Giá trị thị trường (k VNĐ)"]: "{:,.2f}",
                t["headers"]["Lãi/Lỗ (k VNĐ)"]: "{:,.2f}",
                t["headers"]["Lãi/Lỗ (%)"]: "{:+.2f}%",
                t["headers"]["Ngưỡng cảnh báo (%)"]: "±{:.1f}%"
            }).map(highlight_pl, subset=[t["headers"]["Lãi/Lỗ (k VNĐ)"], t["headers"]["Lãi/Lỗ (%)"]]),
            use_container_width=True,
            hide_index=True
        )
        
        # Vẽ biểu đồ cơ cấu danh mục
        st.markdown("<br>", unsafe_allow_html=True)
        st.write(t["portfolio_structure"])
        st.bar_chart(df_display.set_index(t["headers"]["Mã CK"])[t["headers"]["Giá trị thị trường (k VNĐ)"]])
        
    else:
        st.info(t["empty_portfolio"])
        
    st.markdown("---")
    
    # Sentinel Controller & Settings
    st.subheader(t["sentinel_header"])
    sc_col1, sc_col2 = st.columns(2)
    with sc_col1:
        st.info(t["sentinel_info"])
        if st.button(t["manual_scan_btn"]):
            with st.spinner(t["scanning"]):
                scan_res = run_market_scan()
                if scan_res["status"] == "success":
                    st.success(scan_res["message"])
                else:
                    st.error(scan_res["message"])
                    
    with sc_col2:
        st.write(t["update_portfolio_header"])
        with st.form("portfolio_form"):
            form_symbol = st.text_input(t["stock_code"], max_chars=10).upper().strip()
            form_col1, form_col2 = st.columns(2)
            with form_col1:
                form_vol = st.number_input(t["quantity"], min_value=1, step=100, value=100)
                form_cost = st.number_input(t["cost_basis"], min_value=1.0, step=1.0, value=70.0)
            with form_col2:
                form_thresh = st.number_input(t["alert_thresh"], min_value=0.5, step=0.5, value=3.0)
                form_action = st.selectbox(t["action"], [t["add_update"], t["delete"]])
                
            submitted = st.form_submit_button(t["confirm_btn"])
            if submitted:
                if not form_symbol:
                    st.warning(t["enter_symbol"])
                else:
                    if form_action == t["add_update"]:
                        res = add_to_portfolio(form_symbol, int(form_vol), float(form_cost), float(form_thresh))
                    else:
                        res = remove_from_portfolio(form_symbol)
                    
                    if res["status"] == "success":
                        st.success(res["message"])
                        st.rerun()
                    else:
                        st.error(res["message"])

with col2:
    st.subheader(t["chatbot_header"])
    
    # Hiển thị lời chào mặc định nếu lịch sử chat trống
    if not st.session_state.chat_history:
        welcome_msg = t["welcome_msg"]
        st.session_state.chat_history.append({"role": "assistant", "content": welcome_msg})
    
    # Hiển thị lịch sử chat
    for chat in st.session_state.chat_history:
        with st.chat_message(chat["role"]):
            st.markdown(chat["content"])
            
    # Hộp nhập tin nhắn
    user_input = st.chat_input(t["chat_placeholder"])
    
    if user_input:
        # In tin nhắn người dùng lên chat
        with st.chat_message("user"):
            st.markdown(user_input)
        st.session_state.chat_history.append({"role": "user", "content": user_input})
        
        # Gọi Agent phản hồi
        with st.chat_message("assistant"):
            with st.spinner(t["thinking"]):
                try:
                    # Gửi thêm System prefix để ép buộc Agent sử dụng đúng ngôn ngữ được chọn
                    system_prefix = f"[System instruction: The user preferred interface language is {lang}. Please converse and respond ONLY in {lang}. Keep the context.]\n"
                    
                    message = types.Content(
                        role="user", parts=[types.Part.from_text(text=system_prefix + user_input)]
                    )
                    
                    # Chạy runner
                    events = list(
                        st.session_state.runner.run(
                            new_message=message,
                            user_id="default_user",
                            session_id=st.session_state.session.id,
                        )
                    )
                    
                    # Thu thập text phản hồi
                    response_texts = []
                    for event in events:
                        if event.content and event.content.parts:
                            for part in event.content.parts:
                                if part.text:
                                    response_texts.append(part.text)
                                    
                    agent_reply = "".join(response_texts)
                    if not agent_reply:
                        agent_reply = t["no_response"]
                        
                    st.markdown(agent_reply)
                    st.session_state.chat_history.append({"role": "assistant", "content": agent_reply})
                    
                except Exception as e:
                    st.error(f"{t['error_agent']}{e}")

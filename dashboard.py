import streamlit as st
import pandas as pd
import numpy as np
import os
import sys
import json
import time
import plotly.graph_objects as go

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

from app.tools import (
    get_portfolio,
    add_to_portfolio,
    remove_from_portfolio,
    get_stock_quote,
    run_market_scan,
    optimize_portfolio,
    recommend_vn30_stocks,
    clear_portfolio
)
from app.agent import root_agent
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types

# Translation Dictionary gộp cả Agent Chatbot và MPT Định lượng song ngữ hoàn chỉnh
TRANSLATIONS = {
    "English": {
        "page_title": "💰 Personal Wealth Concierge & Sentinel Dashboard",
        "title": "💰 Personal Wealth Concierge & Sentinel",
        "portfolio_header": "📊 Personal Portfolio",
        "total_cost": "Total Cost Value",
        "total_market": "Total Market Value",
        "total_pl": "Total Unrealized P&L",
        "empty_portfolio": "Your portfolio is currently empty. Add stocks using the form below.",
        "portfolio_structure": "📈 **Portfolio Structure by Market Value**",
        "sentinel_header": "⏰ Sentinel System (Monitoring & Email Alerts)",
        "sentinel_info": "Sentinel system scans your portfolio and checks volatility alerts.",
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
        "mpt_sidebar_header": "📈 Markowitz Settings",
        "rf_label": "Risk-Free Rate (Rf %/year)",
        "tolerance_label": "Rebalancing Tolerance (±%)",
        "optimization_section": "📈 Portfolio Optimization & Management (Markowitz MPT)",
        "mpt_tab_ef": "Tab 1: Efficient Frontier",
        "mpt_tab_cal": "Tab 2: Capital Allocation Line (CAL)",
        "mpt_tab_weights": "Tab 3: Optimal Portfolio",
        "opt_return_slider": "Target Expected Return (Ep %/year)",
        "confirm_clear_label": "Check to confirm clearing the entire portfolio",
        "clear_btn": "🗑️ Clear Entire Portfolio",
        "vn30_total_cap_label": "💰 Total Investment Capital (VND)",
        "vn30_target_ret_label": "📈 Target Expected Return Ep (%/year)",
        "vn30_enter_warning": "⚠️ Please enter **Total Capital (> 0 VND)** and **Expected Return (> 0%/year)** to activate VN30 analysis.",
        "vn30_analyze_btn": "🔎 Start VN30 Basket Analysis",
        "vn30_help_cap": "Enter total capital in VND (e.g. 100,000,000)",
        "vn30_help_ep": "Enter expected return rate per year (e.g. 15.0)",
        "vn30_allocation_simulation": "📈 **Simulated Capital Allocation (Markowitz Optimization):**",
        "vn30_add_all_btn": "📥 Add all optimal VN30 stocks to portfolio",
        "max_risk_label": "🛡️ Max Acceptable Risk Ceiling (%/year)",
        "max_risk_help": "Enter maximum acceptable annual risk (volatility) in % (e.g. 20.0)",
        "risk_warning": "⚠️ **Risk Ceiling Exceeded:** The optimized portfolio risk of **{vol:.2f}%** exceeds your risk tolerance ceiling of **{ceiling:.2f}%**.",
        "risk_suggestion_return": "💡 **Suggestion:** To satisfy the risk ceiling of **{ceiling:.2f}%**, you should reduce your Target Expected Return (Ep) to about **{suggested_ep:.2f}%**.",
        "risk_suggestion_min_risk": "💡 **Suggestion:** The minimum achievable risk of this asset pool is **{min_risk:.2f}%** (which exceeds your ceiling of **{ceiling:.2f}%**). You must increase your risk ceiling to at least **{min_risk:.2f}%** to obtain a feasible portfolio.",
        "risk_ok_annotation": "🛡️ **Risk Status:** The optimized portfolio risk of **{vol:.2f}%** is within your acceptable limit (<= **{ceiling:.2f}%**).",
        "start_rebalance_btn": "🔄 Start Portfolio Rebalancing",
        "confirm_rebalance_checkbox": "I agree to execute the above rebalancing transactions.",
        "execute_rebalance_btn": "🚀 Confirm & Execute Rebalancing",
        "rebalance_success": "Portfolio successfully rebalanced!",
        "preview_rebalance_title": "📋 Rebalancing Transactions Preview (Lot of 100)",
        "chatbot_header": "💬 Personal Wealth Concierge",
        "welcome_msg": "Xin chào Mr.Híu! I am your **Personal Wealth Concierge & Sentinel**. I can help you manage your portfolio, analyze stock quotes and news, and trigger volatility scan alerts. How can I assist you today?",
        "chat_placeholder": "Type your request (e.g., 'Add stock VCB to portfolio', or 'Analyze symbol FPT')",
        "thinking": "Concierge is thinking and analyzing...",
        "error_agent": "An error occurred while communicating with the Agent: ",
        "no_response": "Sorry, I did not receive a response from the system.",
        
        # Keys mở rộng cho song ngữ định lượng
        "rebalance_tab": "Rebalancing / Portfolio Realignment",
        "currency_unit": "k VND",
        "alert_warning_toast": "⚠️ **{symbol}**: Current price `{current_price:.2f} {unit}` fluctuated `{sign}{diff_pct:.2f}%` vs cost `{cost_basis:.2f} {unit}` (exceeded alert threshold `±{threshold:.1f}%`)",
        "no_alert_found": "No stock exceeded the alert threshold.",
        "vn30_analysis_desc": "Download 2-year VN30 historical data and select 5 stocks with the best Sharpe Ratio for capital allocation simulation.",
        "vn30_top5_header": "📊 **Top 5 Best Recommended VN30 Stocks:**",
        "vn30_allocation_summary": "📊 **Allocation Summary:** \n* Allocation Type: `{alloc_type}`\n* Total Capital: **{cap_val:,.0f} VND** | Actual Allocated: **{actual_allocated:,.0f} VND**\n* Remaining Cash (lot of 100): **{remaining_cash:,.0f} VND**",
        "vn30_frontier_desc": "📈 **VN30 Efficient Frontier:** Expected risk from **{min_risk:.2f}%** to **{max_risk:.2f}%**.",
        "suggest_adjust_risk": "🛡️ **Note:** With risk ceiling **{ceiling:.2f}%**, the maximum expected return from this pool is **{suggested_ep:.2f}%** (your target Ep is **{target_ep:.2f}%**).",
        "individual_assets_plot": "Individual Assets",
        "efficient_frontier_plot": "Efficient Frontier (EF)",
        "cal_line_plot": "Capital Allocation Line (CAL)",
        "tangency_portfolio_plot": "Tangency Portfolio",
        "gmv_plot": "GMV",
        "selected_target_plot": "Selected Target",
        "opt_port_warning": "💡 Add at least 2 stocks to portfolio to activate Markowitz MPT optimization and rebalancing.",
        "rebalance_summary_header": "🔄 Rebalancing & Asset Weight Realignment",
        "buy_action": "➕ BUY MORE",
        "sell_action": "➖ SELL PART",
        "sell_all_action": "❌ SELL ALL",
        "buy_recommend_msg": "➕ **BUY MORE** approx **{qty_diff:,.0f}** shares of **{symbol}** (to increase weight by `{diff:+.2f}%`)",
        "sell_recommend_msg": "➖ **SELL PART** approx **{qty_diff:,.0f}** shares of **{symbol}** (to decrease weight by `{diff:+.2f}%`)",
        "rebalance_balanced_msg": "✅ Your portfolio is well-balanced. All deviations are within your tolerance band (±{tolerance}%).",
        "plot_x_axis": "Volatility (Stdev) (%)",
        "plot_y_axis": "Expected Return (%)",
        
        # Headers cho các bảng hiển thị
        "headers_recs": {
            "symbol": "Symbol",
            "return": "Annual Return (%)",
            "volatility": "Annual Risk (%)",
            "sharpe": "Sharpe Ratio"
        },
        "headers_alloc": {
            "Mã CK": "Symbol",
            "Tỷ trọng tối ưu": "Optimal Weight",
            "Số lượng phân bổ": "Allocated Qty",
            "Giá hiện tại (k VNĐ)": "Current Price (k VND)",
            "Giá trị phân bổ (k VNĐ)": "Allocated Value (k VND)",
            "Tỷ trọng thực tế": "Actual Weight"
        },
        "headers_comp": {
            "Mã CK": "Symbol",
            "Tỷ trọng hiện tại": "Current Weight",
            "Tỷ trọng tối ưu": "Optimal Weight",
            "Sai lệch tỷ trọng": "Weight Deviation"
        },
        "headers_preview": {
            "Mã CK": "Symbol",
            "Hành động": "Action",
            "Số lượng giao dịch": "Trade Qty",
            "Đơn giá hiện tại (k VNĐ)": "Current Price (k VND)",
            "Giá vốn cũ (k VNĐ)": "Old Cost Basis (k VND)",
            "Giá vốn mới (k VNĐ)": "New Cost Basis (k VND)"
        },
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
        "title": "💰 Trợ lý Quản lý Tài sản & Sentinel",
        "portfolio_header": "📊 Danh mục tài sản cá nhân",
        "total_cost": "Tổng giá trị vốn",
        "total_market": "Tổng giá trị thị trường",
        "total_pl": "Tổng Lãi/Lỗ chưa thực hiện",
        "empty_portfolio": "Danh mục đầu tư hiện đang trống. Hãy thêm cổ phiếu ở bảng điều khiển bên dưới.",
        "portfolio_structure": "📈 **Cơ cấu danh mục theo Giá trị thị trường**",
        "sentinel_header": "⏰ Hệ thống Sentinel (Giám sát & Email Cảnh báo)",
        "sentinel_info": "Hệ thống Sentinel thực hiện giám sát biến động giá của danh mục và gửi email tự động.",
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
        "mpt_sidebar_header": "📈 Cấu hình Markowitz",
        "rf_label": "Lãi suất phi rủi ro (Rf %/năm)",
        "tolerance_label": "Ngưỡng lệch tái cân bằng (±%)",
        "optimization_section": "📈 Tối ưu hóa & Quản trị Danh mục (Markowitz)",
        "mpt_tab_ef": "Tab 1: Đường Biên Hiệu Quả",
        "mpt_tab_cal": "Tab 2: CAL - Đường Phân Bổ Vốn",
        "mpt_tab_weights": "Tab 3: Danh Mục Đầu Tư Tối Ưu",
        "opt_return_slider": "Tỷ suất sinh lời mục tiêu (Ep %/năm)",
        "confirm_clear_label": "Tôi xác nhận muốn xóa toàn bộ danh mục tài sản cá nhân hiện có.",
        "clear_btn": "🗑️ Xóa toàn bộ danh mục",
        "vn30_total_cap_label": "💰 Tổng vốn đầu tư (VNĐ)",
        "vn30_target_ret_label": "📈 Tỷ suất sinh lời kỳ vọng Ep (%/năm)",
        "vn30_enter_warning": "⚠️ Vui lòng nhập **Tổng vốn đầu tư (> 0 VNĐ)** và **Tỷ suất sinh lời kỳ vọng (> 0%/năm)** để kích hoạt phân tích rổ VN30.",
        "vn30_analyze_btn": "🔎 Bắt đầu phân tích rổ VN30",
        "vn30_help_cap": "Nhập tổng nguồn vốn đầu tư bằng VNĐ (ví dụ: 100,000,000)",
        "vn30_help_ep": "Nhập tỷ suất sinh lời kỳ vọng hàng năm (ví dụ: 15.0)",
        "vn30_allocation_simulation": "📈 **Mô phỏng phân bổ vốn (Tối ưu hóa Markowitz):**",
        "vn30_add_all_btn": "📥 Thêm toàn bộ cổ phiếu VN30 tối ưu vào danh mục",
        "max_risk_label": "🛡️ Trần rủi ro chấp nhận (%/năm)",
        "max_risk_help": "Nhập mức độ rủi ro (độ biến động) năm tối đa có thể chấp nhận bằng % (ví dụ: 20.0)",
        "risk_warning": "⚠️ **Vượt trần rủi ro:** Rủi ro dự kiến của danh mục tối ưu là **{vol:.2f}%**, vượt quá trần rủi ro chấp nhận của anh (**{ceiling:.2f}%**).",
        "risk_suggestion_return": "💡 **Khuyến nghị:** Để đảm bảo rủi ro $\\le$ **{ceiling:.2f}%**, anh nên giảm Tỷ suất sinh lời kỳ vọng (Ep) xuống mức tối đa là khoảng **{suggested_ep:.2f}%**.",
        "risk_suggestion_min_risk": "💡 **Khuyến nghị:** Rủi ro tối thiểu của rổ tài sản này là **{min_risk:.2f}%** (vượt quá trần rủi ro **{ceiling:.2f}%**). Anh cần nâng trần rủi ro chấp nhận lên tối thiểu **{min_risk:.2f}%** để tìm được danh mục hợp lệ.",
        "risk_ok_annotation": "🛡️ **Trạng thái rủi ro:** Rủi ro dự kiến của danh mục tối ưu là **{vol:.2f}%**, nằm trong ngưỡng an toàn cho phép (<= **{ceiling:.2f}%**).",
        "start_rebalance_btn": "🔄 Bắt đầu tái cân bằng danh mục",
        "confirm_rebalance_checkbox": "Tôi đồng ý thực hiện các giao dịch tái cân bằng trên.",
        "execute_rebalance_btn": "🚀 Xác nhận thực hiện tái cân bằng",
        "rebalance_success": "Đã thực hiện tái cân bằng thành công cho danh mục!",
        "preview_rebalance_title": "📋 Xem trước các giao dịch tái cân bằng (Lô 100)",
        "chatbot_header": "💬 Trợ lý Tài chính Cá nhân",
        "welcome_msg": "Xin chào Mr.Híu! Tôi là **Trợ lý Tài chính Cá nhân & Sentinel**. Tôi có thể giúp anh quản lý danh mục tài sản, tối ưu hóa Markowitz và quét cảnh báo biến động. Anh cần tôi hỗ trợ gì hôm nay?",
        "chat_placeholder": "Nhập yêu cầu (ví dụ: 'Tối ưu danh mục của tôi' hoặc 'Phân tích mã FPT')",
        "thinking": "Trợ lý đang suy nghĩ và tổng hợp thông tin...",
        "error_agent": "Đã xảy ra lỗi khi trao đổi với Agent: ",
        "no_response": "Xin lỗi, tôi không nhận được phản hồi từ hệ thống.",
        
        # Keys mở rộng cho song ngữ định lượng
        "rebalance_tab": "Tái cân bằng / Cân đối lại danh mục",
        "currency_unit": "k VNĐ",
        "alert_warning_toast": "⚠️ **{symbol}**: Giá hiện tại `{current_price:.2f} {unit}` biến động `{sign}{diff_pct:.2f}%` so với giá vốn `{cost_basis:.2f} {unit}` (Vượt ngưỡng cảnh báo `±{threshold:.1f}%`)",
        "no_alert_found": "Không có mã cổ phiếu nào vượt ngưỡng cảnh báo.",
        "vn30_analysis_desc": "Tải dữ liệu lịch sử 2 năm từ Vnstock cho rổ VN30 và chọn ra 5 mã có hiệu suất sinh lời trên rủi ro (Sharpe) tốt nhất để mô phỏng phân bổ vốn.",
        "vn30_top5_header": "📊 **5 cổ phiếu VN30 đề xuất tốt nhất:**",
        "vn30_allocation_summary": "📊 **Tổng kết phân bổ:** \n* Loại phân bổ: `{alloc_type}`\n* Tổng vốn: **{cap_val:,.0f} VNĐ** | Phân bổ thực tế: **{actual_allocated:,.0f} VNĐ**\n* Tiền mặt còn lại (lô chẵn 100): **{remaining_cash:,.0f} VNĐ**",
        "vn30_frontier_desc": "📈 **Biên hiệu quả VN30:** Rủi ro dự kiến từ **{min_risk:.2f}%** đến **{max_risk:.2f}%**.",
        "suggest_adjust_risk": "🛡️ **Chú thích:** Với trần rủi ro **{ceiling:.2f}%**, tỷ suất sinh lời tối đa khả thi từ rổ này là **{suggested_ep:.2f}%** (Ep hiện tại của anh là **{target_ep:.2f}%**).",
        "individual_assets_plot": "Cổ phiếu đơn lẻ",
        "efficient_frontier_plot": "Đường biên hiệu quả (EF)",
        "cal_line_plot": "Đường phân bổ vốn (CAL)",
        "tangency_portfolio_plot": "Danh mục tiếp tuyến",
        "gmv_plot": "GMV",
        "selected_target_plot": "Mục tiêu được chọn",
        "opt_port_warning": "💡 Hãy thêm ít nhất 2 mã cổ phiếu vào danh mục để kích hoạt mô hình tối ưu hóa danh mục Markowitz và đề xuất tái cân bằng.",
        "rebalance_summary_header": "🔄 Tái cân bằng & Phân bổ lại tỷ trọng tài sản",
        "buy_action": "➕ MUA THÊM",
        "sell_action": "➖ BÁN BỚT",
        "sell_all_action": "❌ BÁN HẾT",
        "buy_recommend_msg": "➕ **MUA THÊM** khoảng **{qty_diff:,.0f}** cổ phiếu **{symbol}** (Để tăng tỷ trọng lên `{diff:+.2f}%`)",
        "sell_recommend_msg": "➖ **BÁN BỚT** khoảng **{qty_diff:,.0f}** cổ phiếu **{symbol}** (Để giảm tỷ trọng đi `{diff:+.2f}%`)",
        "rebalance_balanced_msg": "✅ Danh mục của anh rất cân đối. Mọi sai lệch tỷ trọng đều nằm trong ngưỡng chịu đựng cho phép (±{tolerance}%).",
        "plot_x_axis": "Độ biến động (Stdev) (%)",
        "plot_y_axis": "Tỷ suất sinh lời kỳ vọng (%)",
        
        # Headers cho các bảng hiển thị
        "headers_recs": {
            "symbol": "Mã CK",
            "return": "Lợi nhuận năm (%)",
            "volatility": "Rủi ro năm (%)",
            "sharpe": "Sharpe Ratio"
        },
        "headers_alloc": {
            "Mã CK": "Mã CK",
            "Tỷ trọng tối ưu": "Tỷ trọng tối ưu",
            "Số lượng phân bổ": "Số lượng phân bổ",
            "Giá hiện tại (k VNĐ)": "Giá hiện tại (k VNĐ)",
            "Giá trị phân bổ (k VNĐ)": "Giá trị phân bổ (k VNĐ)",
            "Tỷ trọng thực tế": "Tỷ trọng thực tế"
        },
        "headers_comp": {
            "Mã CK": "Mã CK",
            "Tỷ trọng hiện tại": "Tỷ trọng hiện tại",
            "Tỷ trọng tối ưu": "Tỷ trọng tối ưu",
            "Sai lệch tỷ trọng": "Sai lệch tỷ trọng"
        },
        "headers_preview": {
            "Mã CK": "Mã CK",
            "Hành động": "Hành động",
            "Số lượng giao dịch": "Số lượng giao dịch",
            "Đơn giá hiện tại (k VNĐ)": "Đơn giá hiện tại (k VNĐ)",
            "Giá vốn cũ (k VNĐ)": "Giá vốn cũ (k VNĐ)",
            "Giá vốn mới (k VNĐ)": "Giá vốn mới (k VNĐ)"
        },
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

# Khởi tạo trạng thái session state cho đồng bộ hóa Ep và Trần rủi ro
if "target_ep" not in st.session_state:
    st.session_state.target_ep = 10.0

if "vn30_ep_input" not in st.session_state:
    st.session_state.vn30_ep_input = 10.0

if "mpt_slider_ep" not in st.session_state:
    st.session_state.mpt_slider_ep = 10.0

if "max_risk_ceiling" not in st.session_state:
    st.session_state.max_risk_ceiling = 20.0

if "vn30_max_risk_input" not in st.session_state:
    st.session_state.vn30_max_risk_input = 20.0

if "mpt_sidebar_max_risk_input" not in st.session_state:
    st.session_state.mpt_sidebar_max_risk_input = 20.0

if "show_rebalance_preview" not in st.session_state:
    st.session_state.show_rebalance_preview = False

def sync_vn30_to_mpt():
    if "vn30_ep_input" in st.session_state:
        st.session_state.target_ep = st.session_state.vn30_ep_input
        st.session_state.mpt_slider_ep = st.session_state.vn30_ep_input

def sync_mpt_to_vn30():
    if "mpt_slider_ep" in st.session_state:
        st.session_state.target_ep = st.session_state.mpt_slider_ep
        st.session_state.vn30_ep_input = st.session_state.mpt_slider_ep

def sync_vn30_to_sidebar_risk():
    if "vn30_max_risk_input" in st.session_state:
        st.session_state.max_risk_ceiling = st.session_state.vn30_max_risk_input
        st.session_state.mpt_sidebar_max_risk_input = st.session_state.vn30_max_risk_input

def sync_sidebar_to_vn30_risk():
    if "mpt_sidebar_max_risk_input" in st.session_state:
        st.session_state.max_risk_ceiling = st.session_state.mpt_sidebar_max_risk_input
        st.session_state.vn30_max_risk_input = st.session_state.mpt_sidebar_max_risk_input

# Đồng bộ hóa trần rủi ro lúc đầu chạy script trước khi các widget được khởi tạo
if "mpt_sidebar_max_risk_input" in st.session_state and "vn30_max_risk_input" in st.session_state:
    if st.session_state.vn30_max_risk_input != st.session_state.mpt_sidebar_max_risk_input:
        st.session_state.vn30_max_risk_input = st.session_state.mpt_sidebar_max_risk_input
        st.session_state.max_risk_ceiling = st.session_state.mpt_sidebar_max_risk_input

# Sidebar settings & Chatbot
st.sidebar.title("⚙️ Cấu hình / Settings")
lang = st.sidebar.selectbox("Language / Ngôn ngữ", ["English", "Tiếng Việt"], index=0)
t = TRANSLATIONS[lang]

# Cấu hình Page toàn màn hình
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

# Khởi tạo trạng thái hội thoại
if "current_lang" not in st.session_state:
    st.session_state.current_lang = lang

if "runner" not in st.session_state or st.session_state.runner.agent.model != root_agent.model or st.session_state.current_lang != lang:
    st.session_state.current_lang = lang
    session_service = InMemorySessionService()
    st.session_state.session_service = session_service
    st.session_state.runner = Runner(agent=root_agent, session_service=session_service, app_name="app")
    st.session_state.session = session_service.create_session_sync(user_id="default_user", app_name="app")
    st.session_state.chat_history = []

# Tham số Markowitz Sidebar
st.sidebar.markdown("---")
st.sidebar.subheader(t["mpt_sidebar_header"])
rf_input = st.sidebar.number_input(t["rf_label"], min_value=0.0, max_value=15.0, value=2.5, step=0.1)
tolerance_input = st.sidebar.number_input(t["tolerance_label"], min_value=1.0, max_value=20.0, value=5.0, step=0.5)
max_risk_input = st.sidebar.number_input(
    t["max_risk_label"],
    min_value=1.0,
    max_value=100.0,
    step=1.0,
    help=t["max_risk_help"],
    key="mpt_sidebar_max_risk_input",
    on_change=sync_sidebar_to_vn30_risk
)

# KHUNG CHATBOT TRỢ LÝ TRÊN SIDEBAR
st.sidebar.markdown("---")
st.sidebar.subheader(t["chatbot_header"])

# Hiển thị lời chào mặc định nếu lịch sử chat trống
if not st.session_state.chat_history:
    welcome_msg = t["welcome_msg"]
    st.session_state.chat_history.append({"role": "assistant", "content": welcome_msg})

# Tạo một container trôi cho chat history trong sidebar
chat_container = st.sidebar.container(height=350)
with chat_container:
    for chat in st.session_state.chat_history:
        with st.chat_message(chat["role"]):
            st.markdown(chat["content"])

# Ô nhập liệu chat của chatbot ở sidebar
user_input = st.sidebar.chat_input(t["chat_placeholder"])

if user_input:
    # Ghi nhận và in tin nhắn người dùng lên chat
    with chat_container:
        with st.chat_message("user"):
            st.markdown(user_input)
    st.session_state.chat_history.append({"role": "user", "content": user_input})
    
    # Gọi Agent phản hồi
    with chat_container:
        with st.chat_message("assistant"):
            with st.spinner(t["thinking"]):
                try:
                    system_prefix = f"[System instruction: The user preferred interface language is {lang}. Please converse and respond ONLY in {lang}. Keep the context.]\n"
                    message = types.Content(
                        role="user", parts=[types.Part.from_text(text=system_prefix + user_input)]
                    )
                    
                    events = list(
                        st.session_state.runner.run(
                            new_message=message,
                            user_id="default_user",
                            session_id=st.session_state.session.id,
                        )
                    )
                    
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
    st.rerun()

# ----------------- PANEL CHÍNH TOÀN MÀN HÌNH -----------------
st.title(t["title"])
st.markdown("---")

# Hàm load danh mục mở rộng
def load_portfolio_details():
    res = get_portfolio()
    if res["status"] != "success":
        return []
    
    portfolio = res["portfolio"]
    detailed_portfolio = []
    
    for item in portfolio:
        symbol = item["symbol"]
        volume = item["volume"]
        cost_basis = item["cost_basis"]
        alert_threshold = item["alert_threshold"]
        
        quote_res = get_stock_quote(symbol)
        current_price = cost_basis
        if quote_res["status"] == "success":
            quote = quote_res["quote"]
            close_price = float(quote.get("close_price", 0))
            if close_price <= 0:
                close_price = float(quote.get("reference_price", 0))
            
            if close_price > 0:
                current_price = close_price / 1000.0
            
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

detailed_portfolio = load_portfolio_details()
df_portfolio = pd.DataFrame(detailed_portfolio)

# Tách 3 Tab giao diện chính dịch động
tab_view, tab_mpt, tab_rebalance = st.tabs([
    f"📊 {t['portfolio_header']}", 
    f"🔎 {t['optimization_section']}", 
    f"🔄 {t['rebalance_tab']}"
])

# ------------- TAB 1: DANH MỤC & SENTINEL -------------
with tab_view:
    col_v1, col_v2 = st.columns([3, 2])
    
    with col_v1:
        st.subheader(t["portfolio_header"])
        if not df_portfolio.empty:
            total_cost_val = df_portfolio["Giá trị vốn (k VNĐ)"].sum()
            total_market_val = df_portfolio["Giá trị thị trường (k VNĐ)"].sum()
            total_pl = total_market_val - total_cost_val
            total_pl_pct = (total_pl / total_cost_val * 100.0) if total_cost_val > 0 else 0
            
            pl_color = "green-text" if total_pl >= 0 else "red-text"
            pl_sign = "+" if total_pl >= 0 else ""
            
            m_col1, m_col2, m_col3 = st.columns(3)
            with m_col1:
                st.markdown(f"<div class='metric-card'><div style='color: #888;'>{t['total_cost']}</div><div class='metric-value'>{total_cost_val:,.2f} {t['currency_unit']}</div></div>", unsafe_allow_html=True)
            with m_col2:
                st.markdown(f"<div class='metric-card'><div style='color: #888;'>{t['total_market']}</div><div class='metric-value'>{total_market_val:,.2f} {t['currency_unit']}</div></div>", unsafe_allow_html=True)
            with m_col3:
                st.markdown(f"<div class='metric-card'><div style='color: #888;'>{t['total_pl']}</div><div class='metric-value {pl_color}'>{pl_sign}{total_pl:,.2f} {t['currency_unit']} ({pl_sign}{total_pl_pct:.2f}%)</div></div>", unsafe_allow_html=True)
                
            st.markdown("<br>", unsafe_allow_html=True)
            
            # Định dạng bảng danh mục
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
            
            st.write(t["portfolio_structure"])
            st.bar_chart(df_display.set_index(t["headers"]["Mã CK"])[t["headers"]["Giá trị thị trường (k VNĐ)"]])
            
            # Xóa danh mục
            clear_confirm = st.checkbox(t["confirm_clear_label"], value=False, key="chk_clear_portfolio")
            if st.button(t["clear_btn"], type="primary", disabled=not clear_confirm):
                clear_res = clear_portfolio()
                if clear_res["status"] == "success":
                    st.success(clear_res["message"])
                    st.rerun()
        else:
            st.info(t["empty_portfolio"])
            
    with col_v2:
        st.subheader(t["sentinel_header"])
        st.info(t["sentinel_info"])
        if st.button(t["manual_scan_btn"]):
            with st.spinner(t["scanning"]):
                scan_res = run_market_scan()
                if scan_res["status"] == "success":
                    st.success(scan_res["message"])
                    # Hiển thị các cảnh báo trực tiếp trên UI
                    if "alerts" in scan_res and scan_res["alerts"]:
                        for alert in scan_res["alerts"]:
                            sign = "+" if alert["diff_pct"] >= 0 else ""
                            st.warning(
                                t["alert_warning_toast"].format(
                                    symbol=alert['symbol'],
                                    current_price=alert['current_price'],
                                    unit=t['currency_unit'],
                                    sign=sign,
                                    diff_pct=alert['diff_pct'],
                                    cost_basis=alert['cost_basis'],
                                    threshold=alert['threshold']
                                )
                            )
                    else:
                        st.info(t["no_alert_found"])
                else:
                    st.error(scan_res["message"])
                    
        st.markdown("---")
        st.write(t["update_portfolio_header"])
        with st.form("portfolio_update_form"):
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

# ------------- TAB 2: PHÂN TÍCH VN30 & OPTIMIZE MARKOWITZ -------------
with tab_mpt:
    st.subheader(f"🔎 {t['optimization_section']}")
    col_m1, col_m2 = st.columns([1, 2])
    
    # 2.1. Phân bổ rổ VN30
    with col_m1:
        st.write(t["vn30_analysis_desc"])
        vn30_total_cap = st.number_input(t["vn30_total_cap_label"], min_value=0, value=100000000, step=10000000)
        st.number_input(
            t["vn30_target_ret_label"],
            min_value=0.0,
            max_value=100.0,
            step=0.5,
            key="vn30_ep_input",
            on_change=sync_vn30_to_mpt
        )
        st.number_input(
            t["max_risk_label"],
            min_value=1.0,
            max_value=100.0,
            step=1.0,
            key="vn30_max_risk_input",
            on_change=sync_vn30_to_sidebar_risk
        )
        
        is_ready = (vn30_total_cap > 0) and (st.session_state.target_ep > 0.0) and (st.session_state.max_risk_ceiling > 0.0)
        if not is_ready:
            st.warning(t["vn30_enter_warning"])
            
        if st.button(t["vn30_analyze_btn"], disabled=not is_ready):
            progress_bar = st.progress(0.0)
            status_text = st.empty()
            
            def update_progress(val, text):
                progress_bar.progress(val)
                status_text.text(text)
                
            rec_res = recommend_vn30_stocks(risk_free_rate_annual=rf_input, progress_callback=update_progress)
            if rec_res["status"] == "success":
                st.success("Hoàn tất phân tích VN30!" if lang == "Tiếng Việt" else "Completed VN30 analysis!")
                st.session_state.vn30_recommendations = rec_res["recommendations"]
                st.session_state.vn30_total_cap_at_analysis = vn30_total_cap
            else:
                st.error(rec_res["message"])
                
    with col_m2:
        if "vn30_recommendations" in st.session_state:
            recs = st.session_state.vn30_recommendations
            st.write(t["vn30_top5_header"])
            df_recs = pd.DataFrame(recs)
            # Rename các cột động
            df_recs_display = df_recs.rename(columns=t["headers_recs"])
            st.dataframe(df_recs_display.style.format({
                t["headers_recs"]["return"]: "{:.2f}%",
                t["headers_recs"]["volatility"]: "{:.2f}%",
                t["headers_recs"]["sharpe"]: "{:.4f}"
            }), use_container_width=True, hide_index=True)
            
            # Chạy MPT trên 5 mã này
            symbols_recs = [item["symbol"] for item in recs]
            opt_res_recs = optimize_portfolio(symbols_recs, risk_free_rate_annual=rf_input, target_return=st.session_state.target_ep)
            
            allocated_portfolio_risk = 0.0
            if opt_res_recs["status"] == "success":
                target_data = opt_res_recs.get("target")
                if target_data and target_data.get("weights") is not None:
                    opt_weights = target_data["weights"]
                    alloc_type = f"Target Ep ({st.session_state.target_ep:.2f}%)"
                    allocated_portfolio_risk = target_data["volatility"]
                else:
                    opt_weights = opt_res_recs["tangency"]["weights"]
                    alloc_type = "Tangency (Max Sharpe - Fallback)"
                    allocated_portfolio_risk = opt_res_recs["tangency"]["volatility"]
            else:
                opt_weights = [0.2] * len(symbols_recs)
                alloc_type = "Equal Weight (Fallback)"
                allocated_portfolio_risk = 0.0
                
            cap_val = st.session_state.get("vn30_total_cap_at_analysis", vn30_total_cap)
            cap_val_k = cap_val / 1000.0
            
            alloc_list = []
            actual_total_spent_k = 0.0
            
            for idx, symbol in enumerate(symbols_recs):
                weight = opt_weights[idx]
                q_res = get_stock_quote(symbol)
                current_p = float(q_res["quote"].get("close_price", 70000.0)) / 1000.0 if q_res["status"] == "success" else 70.0
                
                target_val_i = weight * cap_val_k
                vol = int(target_val_i / current_p / 100) * 100
                actual_val_i = vol * current_p
                actual_total_spent_k += actual_val_i
                
                alloc_list.append({
                    "Mã CK": symbol,
                    "Tỷ trọng tối ưu": f"{weight*100:.2f}%",
                    "Số lượng phân bổ": vol,
                    "Giá hiện tại (k VNĐ)": current_p,
                    "Giá trị phân bổ (k VNĐ)": actual_val_i
                })
                
            for item in alloc_list:
                item["Tỷ trọng thực tế"] = f"{(item['Giá trị phân bổ (k VNĐ)'] / cap_val_k * 100):.2f}%" if cap_val_k > 0 else "0.00%"
                
            df_alloc = pd.DataFrame(alloc_list)
            st.dataframe(df_alloc.rename(columns=t["headers_alloc"]).style.format({
                t["headers_alloc"]["Số lượng phân bổ"]: "{:,}",
                t["headers_alloc"]["Giá hiện tại (k VNĐ)"]: "{:,.2f}",
                t["headers_alloc"]["Giá trị phân bổ (k VNĐ)"]: "{:,.2f}"
            }), use_container_width=True, hide_index=True)
            
            remaining_cash_k = cap_val_k - actual_total_spent_k
            st.write(
                t["vn30_allocation_summary"].format(
                    alloc_type=alloc_type,
                    cap_val=cap_val,
                    actual_allocated=actual_total_spent_k * 1000,
                    remaining_cash=remaining_cash_k * 1000
                )
            )
            
            # Kiểm tra trần rủi ro
            is_risk_exceeded = False
            if opt_res_recs["status"] == "success":
                frontier_data = opt_res_recs["frontier"]
                min_frontier_risk = min(frontier_data["volatilities"])
                max_frontier_risk = max(frontier_data["volatilities"])
                
                st.markdown(t["vn30_frontier_desc"].format(min_risk=min_frontier_risk, max_risk=max_frontier_risk))
                if allocated_portfolio_risk > st.session_state.max_risk_ceiling:
                    is_risk_exceeded = True
                    st.error(t["risk_warning"].format(vol=allocated_portfolio_risk, ceiling=st.session_state.max_risk_ceiling))
                    valid_idx = [i for i, v in enumerate(frontier_data["volatilities"]) if v <= st.session_state.max_risk_ceiling]
                    if valid_idx:
                        best_idx = max(valid_idx, key=lambda i: frontier_data["returns"][i])
                        suggested_ep = frontier_data["returns"][best_idx]
                        st.info(t["risk_suggestion_return"].format(ceiling=st.session_state.max_risk_ceiling, suggested_ep=suggested_ep))
                    else:
                        min_risk = opt_res_recs["gmv"]["volatility"]
                        st.info(t["risk_suggestion_min_risk"].format(min_risk=min_risk, ceiling=st.session_state.max_risk_ceiling))
                else:
                    st.success(t["risk_ok_annotation"].format(vol=allocated_portfolio_risk, ceiling=st.session_state.max_risk_ceiling))
                    
            if st.button(t["vn30_add_all_btn"], type="primary", disabled=is_risk_exceeded):
                success_count = 0
                for item in alloc_list:
                    symbol = item["Mã CK"]
                    vol = item["Số lượng phân bổ"]
                    price = item["Giá hiện tại (k VNĐ)"]
                    if vol >= 100:
                        add_res = add_to_portfolio(symbol, volume=vol, cost_basis=price, alert_threshold=3.0)
                        if add_res["status"] == "success":
                            success_count += 1
                if success_count > 0:
                    st.success(f"Đã thêm thành công {success_count} cổ phiếu vào danh mục!" if lang == "Tiếng Việt" else f"Successfully added {success_count} stocks to portfolio!")
                    st.rerun()

    # 2.2. Vẽ Biên Hiệu Quả và CAL của danh mục tài sản cá nhân hiện có
    st.markdown("---")
    st.subheader("📈 " + t["mpt_tab_ef"] + " & " + t["mpt_tab_cal"])
    symbols_to_opt = [item["Mã CK"] for item in detailed_portfolio] if not df_portfolio.empty else []
    
    if len(symbols_to_opt) >= 2:
        opt_res = optimize_portfolio(symbols_to_opt, risk_free_rate_annual=rf_input)
        if opt_res["status"] == "success":
            gmv = opt_res["gmv"]
            tangency = opt_res["tangency"]
            frontier = opt_res["frontier"]
            individual = opt_res["individual_assets"]
            symbols_list = opt_res["symbols"]
            
            min_slider_ret = float(gmv["return"])
            max_slider_ret = float(max([asset["return"] for asset in individual]))
            if max_slider_ret <= min_slider_ret:
                max_slider_ret = min_slider_ret + 10.0
                
            if st.session_state.mpt_slider_ep < min_slider_ret:
                st.session_state.mpt_slider_ep = min_slider_ret
            elif st.session_state.mpt_slider_ep > max_slider_ret:
                st.session_state.mpt_slider_ep = max_slider_ret
            st.session_state.target_ep = st.session_state.mpt_slider_ep
            
            target_ep = st.slider(
                t["opt_return_slider"],
                min_value=min_slider_ret,
                max_value=max_slider_ret,
                format="%.2f%%",
                key="mpt_slider_ep",
                on_change=sync_mpt_to_vn30
            )
            
            opt_res_target = optimize_portfolio(symbols_to_opt, risk_free_rate_annual=rf_input, target_return=target_ep)
            target_portfolio = opt_res_target.get("target") if opt_res_target["status"] == "success" else None
            
            # Kiểm tra trần rủi ro danh mục cá nhân
            if target_portfolio:
                actual_port_risk = target_portfolio["volatility"]
                if actual_port_risk > st.session_state.max_risk_ceiling:
                    st.error(t["risk_warning"].format(vol=actual_port_risk, ceiling=st.session_state.max_risk_ceiling))
                else:
                    st.success(t["risk_ok_annotation"].format(vol=actual_port_risk, ceiling=st.session_state.max_risk_ceiling))
            
            # Vẽ đồ thị kết hợp bằng Plotly (Đã dịch các legend của Đồ thị)
            fig = go.Figure()
            # 1. Efficient Frontier
            fig.add_trace(go.Scatter(
                x=frontier["volatilities"],
                y=frontier["returns"],
                mode="lines",
                name=t["efficient_frontier_plot"],
                line=dict(color="green", width=3)
            ))
            # 2. CAL Line
            cal_returns = np.linspace(rf_input, max_slider_ret, 50)
            cal_vols = [float((r - rf_input) / tangency["sharpe"]) if tangency["sharpe"] > 0 else 0.0 for r in cal_returns]
            fig.add_trace(go.Scatter(
                x=cal_vols,
                y=list(cal_returns),
                mode="lines",
                name=t["cal_line_plot"],
                line=dict(color="orange", width=2, dash="dash")
            ))
            # 3. Tangency Portfolio
            fig.add_trace(go.Scatter(
                x=[tangency["volatility"]],
                y=[tangency["return"]],
                mode="markers+text",
                name=t["tangency_portfolio_plot"],
                marker=dict(color="orange", size=12, symbol="diamond"),
                text=[t["tangency_portfolio_plot"]],
                textposition="top center"
            ))
            # 4. GMV
            fig.add_trace(go.Scatter(
                x=[gmv["volatility"]],
                y=[gmv["return"]],
                mode="markers+text",
                name=t["gmv_plot"],
                marker=dict(color="red", size=10, symbol="star"),
                text=[t["gmv_plot"]],
                textposition="bottom center"
            ))
            # 5. Các tài sản đơn lẻ
            fig.add_trace(go.Scatter(
                x=[asset["volatility"] for asset in individual],
                y=[asset["return"] for asset in individual],
                mode="markers+text",
                name=t["individual_assets_plot"],
                marker=dict(size=8, color="yellow"),
                text=[asset["symbol"] for asset in individual],
                textposition="top center"
            ))
            # 6. Điểm Target được chọn
            if target_portfolio:
                fig.add_trace(go.Scatter(
                    x=[target_portfolio["volatility"]],
                    y=[target_portfolio["return"]],
                    mode="markers",
                    name=t["selected_target_plot"],
                    marker=dict(color="cyan", size=12, symbol="circle-dot")
                ))
                
            fig.update_layout(
                xaxis_title=t["plot_x_axis"],
                yaxis_title=t["plot_y_axis"],
                template="plotly_dark",
                height=500
            )
            st.plotly_chart(fig, use_container_width=True)
    else:
        st.info(t["opt_port_warning"])

# ------------- TAB 3: TÁI CÂN BẰNG DANH MỤC (PORTFOLIO REBALANCING) -------------
with tab_rebalance:
    st.subheader(t["rebalance_summary_header"])
    if len(symbols_to_opt) >= 2:
        opt_res_rebal = optimize_portfolio(symbols_to_opt, risk_free_rate_annual=rf_input, target_return=st.session_state.target_ep)
        if opt_res_rebal["status"] == "success":
            gmv_reb = opt_res_rebal["gmv"]
            tangency_reb = opt_res_rebal["tangency"]
            symbols_list_reb = opt_res_rebal["symbols"]
            target_port_reb = opt_res_rebal.get("target")
            
            # Trọng số tối ưu
            weights_optimal_assets = np.array(target_port_reb["weights"] if target_port_reb else tangency_reb["weights"])
            
            # Tính trọng số hiện tại
            total_market_val = sum([item["Giá trị thị trường (k VNĐ)"] for item in detailed_portfolio])
            weights_current = []
            for symbol in symbols_list_reb:
                item = next((x for x in detailed_portfolio if x["Mã CK"] == symbol), None)
                if item and total_market_val > 0:
                    weights_current.append(item["Giá trị thị trường (k VNĐ)"] / total_market_val)
                else:
                    weights_current.append(0.0)
            weights_current = np.array(weights_current)
            
            # Khuyến nghị Tái cân bằng
            tolerance_decimal = tolerance_input / 100.0
            rebalance_needed = False
            trades_preview = []
            
            # Bảng so sánh đối chiếu trọng số dịch động
            df_comp_data = []
            for idx_i, symbol in enumerate(symbols_list_reb):
                diff = weights_optimal_assets[idx_i] - weights_current[idx_i]
                df_comp_data.append({
                    "Mã CK": symbol,
                    "Tỷ trọng hiện tại": f"{weights_current[idx_i]*100:.2f}%",
                    "Tỷ trọng tối ưu": f"{weights_optimal_assets[idx_i]*100:.2f}%",
                    "Sai lệch tỷ trọng": f"{diff*100:+.2f}%"
                })
            df_comp = pd.DataFrame(df_comp_data).rename(columns=t["headers_comp"])
            st.dataframe(df_comp, use_container_width=True, hide_index=True)
            
            # Tạo chi tiết giao dịch
            for idx_i, symbol in enumerate(symbols_list_reb):
                diff = weights_optimal_assets[idx_i] - weights_current[idx_i]
                item = next((x for x in detailed_portfolio if x["Mã CK"] == symbol), None)
                current_price = item["Giá hiện tại (k VNĐ)"] if item else 1.0
                old_vol = item["Số lượng"] if item else 0
                old_cost = item["Giá vốn (k VNĐ)"] if item else 0.0
                
                target_value_diff = diff * total_market_val
                qty_diff = target_value_diff / current_price if current_price > 0 else 0.0
                adjusted_qty = int(abs(qty_diff) / 100) * 100
                
                if abs(diff) >= tolerance_decimal:
                    rebalance_needed = True
                    if qty_diff > 0:
                        st.success(t["buy_recommend_msg"].format(qty_diff=qty_diff, symbol=symbol, diff=diff*100))
                    elif qty_diff < 0:
                        st.error(t["sell_recommend_msg"].format(qty_diff=abs(qty_diff), symbol=symbol, diff=diff*100))
                
                if adjusted_qty >= 100:
                    if qty_diff > 0:
                        new_vol = old_vol + adjusted_qty
                        new_cost = current_price
                        trades_preview.append({
                            "Mã CK": symbol,
                            "Hành động": t["buy_action"],
                            "Số lượng giao dịch": adjusted_qty,
                            "Đơn giá hiện tại (k VNĐ)": current_price,
                            "Giá vốn cũ (k VNĐ)": old_cost,
                            "Giá vốn mới (k VNĐ)": new_cost,
                            "new_volume": new_vol,
                            "new_cost": new_cost
                        })
                    else:
                        new_vol = max(0, old_vol - adjusted_qty)
                        new_cost = current_price
                        trades_preview.append({
                            "Mã CK": symbol,
                            "Hành động": t["sell_action"] if new_vol > 0 else t["sell_all_action"],
                            "Số lượng giao dịch": adjusted_qty if new_vol > 0 else old_vol,
                            "Đơn giá hiện tại (k VNĐ)": current_price,
                            "Giá vốn cũ (k VNĐ)": old_cost,
                            "Giá vốn mới (k VNĐ)": new_cost if new_vol > 0 else 0.0,
                            "new_volume": new_vol,
                            "new_cost": new_cost
                        })
            
            if not rebalance_needed:
                st.info(t["rebalance_balanced_msg"].format(tolerance=tolerance_input))
                
            if trades_preview:
                st.markdown("<br>", unsafe_allow_html=True)
                if st.button(t["start_rebalance_btn"], key="btn_start_rebalance_main"):
                    st.session_state.show_rebalance_preview = True
                    
                if st.session_state.show_rebalance_preview:
                    st.markdown("---")
                    st.subheader(t["preview_rebalance_title"])
                    df_preview_raw = pd.DataFrame(trades_preview)[["Mã CK", "Hành động", "Số lượng giao dịch", "Đơn giá hiện tại (k VNĐ)", "Giá vốn cũ (k VNĐ)", "Giá vốn mới (k VNĐ)"]]
                    # Rename các cột xem trước giao dịch
                    df_preview = df_preview_raw.rename(columns=t["headers_preview"])
                    
                    st.dataframe(df_preview.style.format({
                        t["headers_preview"]["Số lượng giao dịch"]: "{:,}",
                        t["headers_preview"]["Đơn giá hiện tại (k VNĐ)"]: "{:,.2f}",
                        t["headers_preview"]["Giá vốn cũ (k VNĐ)"]: "{:,.2f}",
                        t["headers_preview"]["Giá vốn mới (k VNĐ)"]: "{:,.2f}"
                    }), use_container_width=True, hide_index=True)
                    
                    confirm_rebalance = st.checkbox(t["confirm_rebalance_checkbox"], key="chk_confirm_rebalance_main")
                    if st.button(t["execute_rebalance_btn"], type="primary", disabled=not confirm_rebalance, key="btn_execute_rebalance_main"):
                        success_actions = 0
                        for t_item in trades_preview:
                            sym = t_item["Mã CK"]
                            old_item = next((x for x in detailed_portfolio if x["Mã CK"] == sym), None)
                            old_thresh = old_item["Ngưỡng cảnh báo (%)"] if old_item else 3.0
                            
                            if t_item["new_volume"] > 0:
                                add_res = add_to_portfolio(sym, volume=int(t_item["new_volume"]), cost_basis=float(t_item["new_cost"]), alert_threshold=float(old_thresh))
                                if add_res["status"] == "success":
                                    success_actions += 1
                            else:
                                rem_res = remove_from_portfolio(sym)
                                if rem_res["status"] == "success":
                                    success_actions += 1
                        if success_actions > 0:
                            st.success(t["rebalance_success"])
                            st.session_state.show_rebalance_preview = False
                            time.sleep(1)
                            st.rerun()
    else:
        st.info(t["opt_port_warning"])

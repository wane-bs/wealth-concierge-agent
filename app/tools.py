import os
import json
import smtplib
import time
import re
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import vnstock as vs

def validate_symbol(symbol: str) -> bool:
    """Xác thực mã chứng khoán (chỉ gồm 3-6 ký tự chữ và số)."""
    if not isinstance(symbol, str):
        return False
    return bool(re.match(r"^[A-Z0-9]{3,6}$", symbol.upper().strip()))

# Hỗ trợ Streamlit Caching an toàn
def st_cache_data_if_available(ttl=None):
    """Decorator tùy chỉnh để áp dụng st.cache_data nếu đang chạy trong tiến trình Streamlit."""
    try:
        from streamlit.runtime import exists as st_exists
        if st_exists():
            import streamlit as st
            return st.cache_data(ttl=ttl)
    except (ImportError, Exception):
        pass
    return lambda f: f

@st_cache_data_if_available(ttl=60)
def get_stock_quote_cached(symbol: str):
    """Tải thông tin giá hiện tại và các chỉ số giao dịch trực tuyến thời gian thực từ vnstock."""
    import time
    m = vs.Market()
    max_retries = 3
    for retry in range(max_retries):
        try:
            df = m.equity(symbol).quote()
            if df is not None and not df.empty:
                # Giãn cách 0.5 giây sau mỗi cuộc gọi API thành công để tránh rate limit
                time.sleep(0.5)
                return df
        except BaseException as e:
            try:
                from streamlit.runtime import exists as st_exists
                if st_exists():
                    import streamlit as st
                    st.toast(f"⚠️ Chạm hạn mức API Vnstock khi lấy báo giá {symbol}. Đang chờ 60s để phục hồi...", icon="⏳")
            except:
                pass
            if retry < max_retries - 1:
                time.sleep(60.0)
            else:
                raise e
    return None

@st_cache_data_if_available(ttl=3600)
def get_single_stock_historical_data_cached(symbol: str, start_date: str, end_date: str):
    """Tải chuỗi dữ liệu giá đóng cửa lịch sử từ vnstock cho một mã cổ phiếu duy nhất."""
    import time
    m = vs.Market()
    max_retries = 3
    for retry in range(max_retries):
        try:
            df = m.equity(symbol).ohlcv(start=start_date, end=end_date, resolution="1D", count=1000)
            if df is not None and not df.empty:
                # Giãn cách 1.5 giây sau mỗi cuộc gọi API thành công để tránh rate limit
                time.sleep(1.5)
                return df
        except BaseException as e:
            try:
                from streamlit.runtime import exists as st_exists
                if st_exists():
                    import streamlit as st
                    st.toast(f"⚠️ Chạm hạn mức API Vnstock khi tải {symbol}. Đang chờ 60s để phục hồi...", icon="⏳")
            except:
                pass
            if retry < max_retries - 1:
                time.sleep(60.0)
            else:
                raise e
    return None

# Đường dẫn file danh mục
PORTFOLIO_FILE = os.path.join(os.path.dirname(__file__), "portfolio.json")

def get_portfolio() -> dict:
    """Đọc và trả về toàn bộ danh sách cổ phiếu trong danh mục đầu tư cá nhân.
    
    Returns:
        dict: Chứa danh sách cổ phiếu và trạng thái thành công.
    """
    try:
        if not os.path.exists(PORTFOLIO_FILE):
            return {"status": "success", "portfolio": []}
        with open(PORTFOLIO_FILE, "r", encoding="utf-8") as f:
            portfolio = json.load(f)
        return {"status": "success", "portfolio": portfolio}
    except Exception as e:
        return {"status": "error", "message": str(e)}

def add_to_portfolio(symbol: str, volume: int, cost_basis: float, alert_threshold: float) -> dict:
    """Thêm một mã cổ phiếu mới hoặc cập nhật một cổ phiếu có sẵn trong danh mục đầu tư.
    
    Args:
        symbol: Mã cổ phiếu viết hoa (ví dụ: FPT, TCB, VCB).
        volume: Số lượng cổ phiếu nắm giữ (phải là số nguyên dương).
        cost_basis: Giá vốn mua vào của cổ phiếu (đơn vị: nghìn VNĐ, ví dụ: 70.5).
        alert_threshold: Ngưỡng cảnh báo biến động theo phần trăm (ví dụ: 3.0 cho mức +/-3%).
        
    Returns:
        dict: Kết quả thực hiện.
    """
    if not validate_symbol(symbol):
        return {"status": "error", "message": f"Mã chứng khoán không hợp lệ: '{symbol}'. Mã phải từ 3 đến 6 ký tự chữ và số."}
    try:
        volume = int(volume)
        cost_basis = float(cost_basis)
        alert_threshold = float(alert_threshold)
    except (ValueError, TypeError):
        return {"status": "error", "message": "Các tham số số lượng, giá vốn và ngưỡng cảnh báo phải có kiểu số hợp lệ."}

    if volume <= 0:
        return {"status": "error", "message": "Số lượng cổ phiếu phải là số nguyên dương lớn hơn 0."}
    if cost_basis <= 0:
        return {"status": "error", "message": "Giá vốn mua vào phải lớn hơn 0."}
    if alert_threshold <= 0:
        return {"status": "error", "message": "Ngưỡng cảnh báo biến động phải lớn hơn 0."}

    try:
        symbol = symbol.upper().strip()
        portfolio = []
        if os.path.exists(PORTFOLIO_FILE):
            with open(PORTFOLIO_FILE, "r", encoding="utf-8") as f:
                portfolio = json.load(f)
        
        # Cập nhật nếu đã tồn tại, ngược lại thêm mới
        found = False
        for item in portfolio:
            if item["symbol"] == symbol:
                item["volume"] = volume
                item["cost_basis"] = cost_basis
                item["alert_threshold"] = alert_threshold
                found = True
                break
        if not found:
            portfolio.append({
                "symbol": symbol,
                "volume": volume,
                "cost_basis": cost_basis,
                "alert_threshold": alert_threshold
            })
            
        with open(PORTFOLIO_FILE, "w", encoding="utf-8") as f:
            json.dump(portfolio, f, indent=2, ensure_ascii=False)
            
        return {"status": "success", "message": f"Đã thêm/cập nhật mã {symbol} vào danh mục."}
    except Exception as e:
        return {"status": "error", "message": str(e)}

def remove_from_portfolio(symbol: str) -> dict:
    """Xóa một mã cổ phiếu khỏi danh mục đầu tư cá nhân.
    
    Args:
        symbol: Mã cổ phiếu cần xóa (ví dụ: FPT).
        
    Returns:
        dict: Kết quả thực hiện.
    """
    if not validate_symbol(symbol):
        return {"status": "error", "message": f"Mã chứng khoán không hợp lệ: '{symbol}'."}
    try:
        symbol = symbol.upper().strip()
        if not os.path.exists(PORTFOLIO_FILE):
            return {"status": "error", "message": "Danh mục chưa tồn tại."}
            
        with open(PORTFOLIO_FILE, "r", encoding="utf-8") as f:
            portfolio = json.load(f)
            
        new_portfolio = [item for item in portfolio if item["symbol"] != symbol]
        if len(new_portfolio) == len(portfolio):
            return {"status": "error", "message": f"Không tìm thấy mã {symbol} trong danh mục."}
            
        with open(PORTFOLIO_FILE, "w", encoding="utf-8") as f:
            json.dump(new_portfolio, f, indent=2, ensure_ascii=False)
            
        return {"status": "success", "message": f"Đã xóa mã {symbol} khỏi danh mục."}
    except Exception as e:
        return {"status": "error", "message": str(e)}

def get_stock_quote(symbol: str) -> dict:
    """Lấy thông tin giá hiện tại và các chỉ số giao dịch trực tuyến thời gian thực của cổ phiếu.
    
    Args:
        symbol: Mã cổ phiếu cần lấy báo giá (ví dụ: FPT).
        
    Returns:
        dict: Chứa dữ liệu báo giá trực tiếp từ thị trường.
    """
    if not validate_symbol(symbol):
        return {"status": "error", "message": f"Mã chứng khoán không hợp lệ: '{symbol}'."}
    try:
        symbol = symbol.upper().strip()
        df = get_stock_quote_cached(symbol)
        if df is None or df.empty:
            return {"status": "error", "message": f"Không có dữ liệu báo giá cho mã {symbol}."}
        # Chuyển đổi dòng đầu tiên thành dict
        quote_data = df.iloc[0].to_dict()
        # Đảm bảo các kiểu dữ liệu số được tuần tự hóa đúng
        for k, v in quote_data.items():
            if hasattr(v, 'item'):  # Chuyển numpy types sang python types
                quote_data[k] = v.item()
        return {"status": "success", "quote": quote_data}
    except Exception as e:
        return {"status": "error", "message": str(e)}

def get_stock_news(symbol: str) -> dict:
    """Lấy danh sách các tin tức và sự kiện doanh nghiệp mới nhất liên quan đến cổ phiếu.
    
    Args:
        symbol: Mã cổ phiếu cần tra cứu tin tức (ví dụ: FPT).
        
    Returns:
        dict: Chứa danh sách tin tức mới nhất.
    """
    if not validate_symbol(symbol):
        return {"status": "error", "message": f"Mã chứng khoán không hợp lệ: '{symbol}'."}
    try:
        symbol = symbol.upper().strip()
        ref = vs.Reference()
        df = ref.company(symbol).news()
        if df.empty:
            return {"status": "success", "news": []}
        
        # Lấy tối đa 5 tin tức gần nhất
        news_list = df.head(5).to_dict(orient="records")
        return {"status": "success", "news": news_list}
    except Exception as e:
        return {"status": "error", "message": str(e)}

def get_financial_ratios(symbol: str) -> dict:
    """Lấy các chỉ số tài chính cơ bản và các thước đo định giá (P/E, P/B, EPS, BVPS) của doanh nghiệp.
    
    Args:
        symbol: Mã cổ phiếu cần lấy chỉ số tài chính (ví dụ: FPT).
        
    Returns:
        dict: Báo cáo chỉ số tài chính 4 kỳ gần nhất.
    """
    if not validate_symbol(symbol):
        return {"status": "error", "message": f"Mã chứng khoán không hợp lệ: '{symbol}'."}
    try:
        symbol = symbol.upper().strip()
        f = vs.Fundamental()
        df = f.equity(symbol).ratio()
        if df.empty:
            return {"status": "error", "message": f"Không có chỉ số tài chính cho mã {symbol}."}
        
        # Lấy 10 dòng chỉ số tiêu biểu
        ratios_list = df.head(10).to_dict(orient="records")
        return {"status": "success", "ratios": ratios_list}
    except Exception as e:
        return {"status": "error", "message": str(e)}

def send_email_alert(subject: str, body: str) -> dict:
    """Gửi một email thông báo hoặc cảnh báo tài chính tới địa chỉ nhận của người dùng qua giao thức SMTP.
    
    Args:
        subject: Tiêu đề email.
        body: Nội dung chi tiết của email (hỗ trợ văn bản thuần hoặc HTML).
        
    Returns:
        dict: Trạng thái gửi thư thành công hay thất bại.
    """
    # Đọc cấu hình từ môi trường
    smtp_server = os.environ.get("SMTP_SERVER", "smtp.gmail.com")
    try:
        smtp_port = int(os.environ.get("SMTP_PORT", "587"))
    except:
        smtp_port = 587
    smtp_user = os.environ.get("SMTP_USER")
    smtp_password = os.environ.get("SMTP_PASSWORD")
    recipient_email = os.environ.get("RECIPIENT_EMAIL")

    if not smtp_user or not smtp_password or not recipient_email:
        return {
            "status": "error", 
            "message": "Cấu hình SMTP chưa hoàn chỉnh trong tệp .env (Thiếu SMTP_USER, SMTP_PASSWORD hoặc RECIPIENT_EMAIL)."
        }

    try:
        msg = MIMEMultipart()
        msg["From"] = smtp_user
        msg["To"] = recipient_email
        msg["Subject"] = subject
        msg.attach(MIMEText(body, "html" if "<html" in body.lower() else "plain"))

        # Thiết lập kết nối SMTP
        server = smtplib.SMTP(smtp_server, smtp_port)
        server.starttls()
        server.login(smtp_user, smtp_password)
        server.sendmail(smtp_user, recipient_email, msg.as_string())
        server.quit()

        return {"status": "success", "message": f"Đã gửi email cảnh báo tới {recipient_email}."}
    except Exception as e:
        return {"status": "error", "message": f"Lỗi kết nối hoặc gửi email qua SMTP: {str(e)}"}

def run_market_scan() -> dict:
    """Quét toàn bộ danh mục cổ phiếu, kiểm tra biến động giá thời gian thực và tự động gửi email cảnh báo nếu có mã vượt ngưỡng.
    
    Returns:
        dict: Kết quả quét và danh sách các mã bị cảnh báo.
    """
    try:
        portfolio_res = get_portfolio()
        if portfolio_res["status"] != "success":
            return portfolio_res
        
        portfolio = portfolio_res["portfolio"]
        if not portfolio:
            return {"status": "success", "message": "Danh mục trống, không cần quét.", "alerts": []}
            
        alerts = []
        
        for item in portfolio:
            symbol = item["symbol"]
            cost_basis = item["cost_basis"] # Đơn vị: nghìn VNĐ, ví dụ: 65.0
            alert_threshold = item["alert_threshold"] # Đơn vị: %, ví dụ: 3.0
            
            # Lấy giá trực tiếp qua hàm get_stock_quote để dễ dàng Mocking và tối ưu hóa
            try:
                quote_res = get_stock_quote(symbol)
                if quote_res["status"] != "success":
                    continue
                quote_data = quote_res["quote"]
                # close_price từ API dạng VNĐ (ví dụ 70100), chuyển sang nghìn VNĐ
                current_price = float(quote_data.get("close_price", 0)) / 1000.0
                if current_price == 0:
                    continue
                    
                # Tính biến động so với giá vốn
                diff_pct = (current_price - cost_basis) / cost_basis * 100.0
                
                # So sánh với ngưỡng
                if abs(diff_pct) >= alert_threshold:
                    alerts.append({
                        "symbol": symbol,
                        "cost_basis": cost_basis,
                        "current_price": current_price,
                        "diff_pct": diff_pct,
                        "threshold": alert_threshold,
                        "volume": item["volume"]
                    })
            except Exception as e:
                print(f"Lỗi khi quét mã {symbol}: {e}")
                
        if alerts:
            # Soạn thảo email báo cáo
            subject = f"⚠️ CẢNH BÁO BIẾN ĐỘNG DANH MỤC TÀI CHÍNH ({len(alerts)} MÃ VƯỢT NGƯỠNG)"
            
            body = """
            <html>
            <head>
                <style>
                    table { border-collapse: collapse; width: 100%; font-family: Arial, sans-serif; }
                    th, td { border: 1px solid #dddddd; text-align: left; padding: 8px; }
                    th { background-color: #f2f2f2; }
                    .up { color: green; font-weight: bold; }
                    .down { color: red; font-weight: bold; }
                </style>
            </head>
            <body>
                <h2>Thông báo Cảnh báo Biến động Danh mục</h2>
                <p>Hệ thống giám sát Sentinel phát hiện các mã cổ phiếu trong danh mục của anh có biến động vượt ngưỡng cho phép:</p>
                <table>
                    <tr>
                        <th>Mã CK</th>
                        <th>Số lượng</th>
                        <th>Giá vốn (k VNĐ)</th>
                        <th>Giá hiện tại (k VNĐ)</th>
                        <th>Biến động (%)</th>
                        <th>Ngưỡng (%)</th>
                    </tr>
            """
            
            for a in alerts:
                direction_class = "up" if a["diff_pct"] >= 0 else "down"
                sign = "+" if a["diff_pct"] >= 0 else ""
                body += f"""
                    <tr>
                        <td><b>{a["symbol"]}</b></td>
                        <td>{a["volume"]}</td>
                        <td>{a["cost_basis"]:.2f}</td>
                        <td>{a["current_price"]:.2f}</td>
                        <td class="{direction_class}">{sign}{a["diff_pct"]:.2f}%</td>
                        <td>±{a["threshold"]:.1f}%</td>
                    </tr>
                """
                
            body += """
                </table>
                <p><i>Hệ thống tự động gửi từ Trợ lý Tài chính Cá nhân. Vui lòng kiểm tra lại tài khoản giao dịch để đưa ra quyết định kịp thời.</i></p>
            </body>
            </html>
            """
            
            # Gửi email
            send_res = send_email_alert(subject, body)
            return {
                "status": "success", 
                "message": f"Quét hoàn tất. Phát hiện {len(alerts)} mã vượt ngưỡng. Kết quả gửi email: {send_res['message']}",
                "alerts": alerts
            }
        else:
            return {"status": "success", "message": "Quét hoàn tất. Không có mã nào biến động vượt ngưỡng.", "alerts": []}
            
    except Exception as e:
        return {"status": "error", "message": str(e)}

def get_portfolio_historical_data(symbols: list) -> dict:
    """Tải chuỗi dữ liệu giá đóng cửa lịch sử 2 năm gần nhất từ vnstock cho danh sách các mã cổ phiếu.
    
    Args:
        symbols: Danh sách các mã cổ phiếu (ví dụ: ['FPT', 'VCB', 'ACB']).
        
    Returns:
        dict: Chứa trạng thái, dữ liệu giá đóng cửa xoay chiều và cảnh báo nếu có mã thiếu dữ liệu.
    """
    try:
        import numpy as np
        import pandas as pd
        import datetime
        
        if not symbols:
            return {"status": "success", "prices": pd.DataFrame(), "warnings": []}
            
        end_date = datetime.date.today().strftime("%Y-%m-%d")
        # 2 năm trước (khoảng 730 ngày)
        start_date = (datetime.date.today() - datetime.timedelta(days=365 * 2)).strftime("%Y-%m-%d")
        
        prices_dict = {}
        warnings = []
        
        validated_symbols = []
        for s in symbols:
            if validate_symbol(s):
                validated_symbols.append(s.upper().strip())
            else:
                warnings.append(f"Mã chứng khoán '{s}' không hợp lệ và bị bỏ qua.")
                
        if not validated_symbols:
            return {"status": "error", "message": "Không có mã cổ phiếu hợp lệ nào để tải dữ liệu.", "warnings": warnings}
            
        for symbol in validated_symbols:
            # Gọi hàm cached lấy dữ liệu lịch sử của mã đơn lẻ
            try:
                df = get_single_stock_historical_data_cached(symbol, start_date, end_date)
                if df is None or df.empty:
                    warnings.append(f"Không lấy được dữ liệu lịch sử cho mã {symbol}.")
                    continue
                
                # Chuyển đổi định dạng thời gian
                df['time'] = pd.to_datetime(df['time'])
                df = df.sort_values('time')
                
                # Tìm cột giá đóng cửa (thường là 'close' trong vnstock)
                if 'close' in df.columns:
                    prices_dict[symbol] = df.set_index('time')['close']
                else:
                    warnings.append(f"Mã {symbol} không có cột giá đóng cửa 'close'.")
                    
                # Kiểm tra số ngày dữ liệu
                days_count = len(df)
                if days_count < 400:
                    warnings.append(f"⚠️ Mã {symbol} chỉ có {days_count} ngày giao dịch lịch sử (ngắn hơn 2 năm). Ước lượng rủi ro-lợi nhuận có thể bị lệch.")
            except BaseException as e:
                warnings.append(f"Lỗi khi lấy dữ liệu cho mã {symbol}: {str(e)}")
                
        if not prices_dict:
            return {"status": "error", "message": "Không thể tải dữ liệu lịch sử cho bất kỳ mã cổ phiếu nào.", "warnings": warnings}
            
        # Gộp các chuỗi giá thành một DataFrame chung
        df_prices = pd.DataFrame(prices_dict)
        # Điền các ngày thiếu bằng phương pháp forward fill rồi backward fill
        df_prices = df_prices.ffill().bfill()
        
        return {"status": "success", "prices": df_prices, "warnings": warnings}
    except Exception as e:
        return {"status": "error", "message": str(e), "warnings": []}

def optimize_portfolio(symbols: list, risk_free_rate_annual: float = 2.5, target_return: float = None) -> dict:
    """Tính toán tối ưu hóa danh mục theo lý thuyết Markowitz.
    
    Args:
        symbols: Danh sách các mã cổ phiếu trong danh mục.
        risk_free_rate_annual: Lãi suất phi rủi ro năm (%/năm, ví dụ: 2.5).
        target_return: Lợi nhuận kỳ vọng mục tiêu (%/năm) nếu người dùng trượt chọn.
        
    Returns:
        dict: Chứa trọng số tối ưu (GMV, Tangency, Target), ma trận hiệp phương sai, và Efficient Frontier.
    """
    try:
        risk_free_rate_annual = float(risk_free_rate_annual)
        if target_return is not None:
            target_return = float(target_return)
    except (ValueError, TypeError):
        return {"status": "error", "message": "Lãi suất phi rủi ro và lợi nhuận mục tiêu phải có kiểu số hợp lệ."}
        
    if risk_free_rate_annual < 0:
        return {"status": "error", "message": "Lãi suất phi rủi ro không thể âm."}

    try:
        import numpy as np
        import pandas as pd
        from scipy.optimize import minimize
        
        # 1. Tải dữ liệu lịch sử
        hist_res = get_portfolio_historical_data(symbols)
        if hist_res["status"] != "success":
            return hist_res
            
        df_prices = hist_res["prices"]
        warnings = hist_res["warnings"]
        
        if df_prices.empty or len(df_prices.columns) < 2:
            return {
                "status": "error", 
                "message": "Cần ít nhất 2 mã cổ phiếu có dữ liệu lịch sử để thực hiện tối ưu hóa danh mục.",
                "warnings": warnings
            }
            
        # Tính toán tỷ suất sinh lời log-return hàng ngày
        df_returns = np.log(df_prices / df_prices.shift(1)).dropna()
        
        # Số lượng tài sản thực tế
        actual_symbols = list(df_prices.columns)
        num_assets = len(actual_symbols)
        
        # Tỷ suất sinh lời kỳ vọng hàng ngày và ma trận hiệp phương sai hàng ngày
        mean_returns_daily = df_returns.mean()
        cov_matrix_daily = df_returns.cov()
        
        # Quy đổi ra năm (annualized) - sử dụng 252 ngày giao dịch/năm
        mean_returns_annual = mean_returns_daily * 252
        cov_matrix_annual = cov_matrix_daily * 252
        
        # Lãi suất phi rủi ro năm
        rf_annual = risk_free_rate_annual / 100.0
        
        # Hàm tính toán chỉ số thống kê danh mục
        def portfolio_stats(weights):
            weights = np.array(weights)
            port_return = np.sum(mean_returns_annual * weights)
            port_vol = np.sqrt(np.dot(weights.T, np.dot(cov_matrix_annual, weights)))
            sharpe = (port_return - rf_annual) / port_vol if port_vol > 0 else 0
            return port_return, port_vol, sharpe
            
        # Hàm mục tiêu tối thiểu hóa phương sai
        def minimize_variance(weights):
            return np.dot(weights.T, np.dot(cov_matrix_annual, weights))
            
        # Hàm mục tiêu tối đa hóa Sharpe Ratio (tối thiểu hóa số âm Sharpe)
        def minimize_negative_sharpe(weights):
            return -portfolio_stats(weights)[2]
            
        # Ràng buộc cơ bản: tổng trọng số = 1
        constraints = ({'type': 'eq', 'fun': lambda x: np.sum(x) - 1})
        # Giới hạn trọng số: W_i >= 0 và <= 1 (No short selling)
        bounds = tuple((0, 1) for _ in range(num_assets))
        # Khởi tạo trọng số ban đầu đều nhau
        init_weights = num_assets * [1./num_assets]
        
        # --- A. Tối ưu danh mục GMV (Global Minimum Variance) ---
        res_gmv = minimize(minimize_variance, init_weights, method='SLSQP', bounds=bounds, constraints=constraints)
        weights_gmv = res_gmv.x
        ret_gmv, vol_gmv, sharpe_gmv = portfolio_stats(weights_gmv)
        
        # --- B. Tối ưu danh mục Tangency (Max Sharpe) ---
        res_tangency = minimize(minimize_negative_sharpe, init_weights, method='SLSQP', bounds=bounds, constraints=constraints)
        weights_tangency = res_tangency.x
        ret_tangency, vol_tangency, sharpe_tangency = portfolio_stats(weights_tangency)
        
        # --- C. Tính toán Đường biên hiệu quả (Efficient Frontier) ---
        # Lấy dải lợi nhuận từ GMV return đến tối đa lợi nhuận của tài sản đơn lẻ
        max_asset_return = mean_returns_annual.max()
        min_frontier_ret = ret_gmv
        max_frontier_ret = max(max_asset_return, ret_gmv + 0.05)
        
        frontier_returns = np.linspace(min_frontier_ret, max_frontier_ret, 50)
        frontier_vols = []
        frontier_weights = []
        
        for r in frontier_returns:
            cons = (
                {'type': 'eq', 'fun': lambda x: np.sum(x) - 1},
                {'type': 'eq', 'fun': lambda x: np.sum(mean_returns_annual * x) - r}
            )
            res = minimize(minimize_variance, init_weights, method='SLSQP', bounds=bounds, constraints=cons)
            if res.success:
                frontier_vols.append(np.sqrt(res.fun))
                frontier_weights.append(res.x)
            else:
                frontier_vols.append(None)
                frontier_weights.append(None)
                
        # Lọc bỏ các điểm lỗi
        valid_indices = [i for i, v in enumerate(frontier_vols) if v is not None]
        frontier_returns = frontier_returns[valid_indices]
        frontier_vols = np.array(frontier_vols)[valid_indices]
        frontier_weights = [frontier_weights[i] for i in valid_indices]
        
        # --- D. Tính toán danh mục mục tiêu theo Slider (Target Portfolio) ---
        weights_target = None
        ret_target, vol_target, sharpe_target = None, None, None
        if target_return is not None:
            target_return_decimal = target_return / 100.0
            cons_target = (
                {'type': 'eq', 'fun': lambda x: np.sum(x) - 1},
                {'type': 'eq', 'fun': lambda x: np.sum(mean_returns_annual * x) - target_return_decimal}
            )
            res_target = minimize(minimize_variance, init_weights, method='SLSQP', bounds=bounds, constraints=cons_target)
            if res_target.success:
                weights_target = res_target.x
                ret_target, vol_target, sharpe_target = portfolio_stats(weights_target)
            else:
                # Nếu vượt quá giới hạn của biên hiệu quả, dùng Tangency làm fallback
                weights_target = weights_tangency
                ret_target, vol_target, sharpe_target = ret_tangency, vol_tangency, sharpe_tangency
                
        # Chuẩn bị dữ liệu tài sản đơn lẻ để vẽ đồ thị
        individual_assets = []
        for i, symbol in enumerate(actual_symbols):
            individual_assets.append({
                "symbol": symbol,
                "return": float(mean_returns_annual.iloc[i] * 100.0),
                "volatility": float(np.sqrt(cov_matrix_annual.iloc[i, i]) * 100.0)
            })
            
        return {
            "status": "success",
            "symbols": actual_symbols,
            "warnings": warnings,
            "individual_assets": individual_assets,
            "gmv": {
                "weights": [float(w) for w in weights_gmv],
                "return": float(ret_gmv * 100.0),
                "volatility": float(vol_gmv * 100.0),
                "sharpe": float(sharpe_gmv)
            },
            "tangency": {
                "weights": [float(w) for w in weights_tangency],
                "return": float(ret_tangency * 100.0),
                "volatility": float(vol_tangency * 100.0),
                "sharpe": float(sharpe_tangency)
            },
            "target": {
                "weights": [float(w) for w in weights_target] if weights_target is not None else None,
                "return": float(ret_target * 100.0) if ret_target is not None else None,
                "volatility": float(vol_target * 100.0) if vol_target is not None else None,
                "sharpe": float(sharpe_target) if sharpe_target is not None else None
            } if target_return is not None else None,
            "frontier": {
                "returns": [float(r * 100.0) for r in frontier_returns],
                "volatilities": [float(v * 100.0) for v in frontier_vols],
                "weights": [[float(wi) for wi in w] for w in frontier_weights]
            },
            "cov_matrix": [[float(cov_matrix_annual.iloc[i, j]) for j in range(num_assets)] for i in range(num_assets)]
        }
    except Exception as e:
        return {"status": "error", "message": f"Lỗi tối ưu hóa danh mục: {str(e)}", "warnings": []}

def recommend_vn30_stocks(risk_free_rate_annual: float = 2.5, progress_callback=None) -> dict:
    """Tải dữ liệu VN30 động, tính Sharpe Ratio lịch sử 2 năm và đề xuất 5 cổ phiếu tối ưu nhất.
    
    Args:
        risk_free_rate_annual: Lãi suất phi rủi ro năm (ví dụ: 2.5).
        progress_callback: Hàm callback cập nhật tiến độ cho Streamlit (progress, text).
        
    Returns:
        dict: Chứa danh sách 5 cổ phiếu đề xuất cùng các chỉ số của chúng.
    """
    try:
        import numpy as np
        import pandas as pd
        import datetime
        
        # Tải danh sách rổ VN30 động từ Vnstock
        try:
            listing = vs.Listing()
            vn30_series = listing.symbols_by_group('VN30')
            if vn30_series is not None and not vn30_series.empty:
                vn30_symbols = vn30_series.tolist()
            else:
                raise ValueError("Danh sách VN30 lấy từ Vnstock bị trống.")
        except Exception as e:
            # Fallback tĩnh đầy đủ 30 mã VN30 chuẩn xác nếu API lấy danh sách gặp lỗi
            vn30_symbols = [
                "ACB", "BID", "BSR", "CTG", "FPT", "GAS", "GVR", "HDB", "HPG", "LPB", 
                "MBB", "MSN", "MWG", "PLX", "SAB", "SHB", "SSB", "SSI", "STB", "TCB", 
                "TPB", "VCB", "VHM", "VIB", "VIC", "VJC", "VNM", "VPB", "VPL", "VRE"
            ]
        
        end_date = datetime.date.today().strftime("%Y-%m-%d")
        start_date = (datetime.date.today() - datetime.timedelta(days=365 * 2)).strftime("%Y-%m-%d")
        
        prices_dict = {}
        warnings = []
        
        total_symbols = len(vn30_symbols)
        for i, symbol in enumerate(vn30_symbols):
            symbol = symbol.upper().strip()
            
            if progress_callback:
                progress_callback(float(i) / total_symbols, f"Đang kiểm tra/tải dữ liệu cho mã {symbol} ({i+1}/{total_symbols})...")
            
            try:
                df = get_single_stock_historical_data_cached(symbol, start_date, end_date)
                if df is not None and not df.empty and 'close' in df.columns:
                    df['time'] = pd.to_datetime(df['time'])
                    df = df.sort_values('time')
                    prices_dict[symbol] = df.set_index('time')['close']
                else:
                    warnings.append(f"Mã {symbol} không có dữ liệu close.")
            except BaseException as e:
                warnings.append(f"Lỗi khi lấy dữ liệu cho mã {symbol}: {str(e)}")
        
        if progress_callback:
            progress_callback(1.0, "Đang xử lý tính toán Sharpe Ratio cho rổ VN30...")
            
        if not prices_dict:
            return {"status": "error", "message": "Không thể tải dữ liệu lịch sử cho bất kỳ mã VN30 nào.", "warnings": warnings}
            
        df_prices = pd.DataFrame(prices_dict).ffill().bfill()
        df_returns = np.log(df_prices / df_prices.shift(1)).dropna()
        
        mean_returns_annual = df_returns.mean() * 252
        std_returns_annual = df_returns.std() * np.sqrt(252)
        rf_annual = risk_free_rate_annual / 100.0
        
        sharpe_ratios = (mean_returns_annual - rf_annual) / std_returns_annual
        
        df_metrics = pd.DataFrame({
            "symbol": df_prices.columns,
            "return": mean_returns_annual.values * 100.0,
            "volatility": std_returns_annual.values * 100.0,
            "sharpe": sharpe_ratios.values
        })
        
        # Sắp xếp giảm dần theo Sharpe Ratio
        df_metrics = df_metrics.sort_values("sharpe", ascending=False)
        top_5 = df_metrics.head(5).to_dict(orient="records")
        
        return {"status": "success", "recommendations": top_5, "warnings": warnings}
    except Exception as e:
        return {"status": "error", "message": str(e)}

def clear_portfolio() -> dict:
    """Xóa toàn bộ danh sách cổ phiếu trong danh mục đầu tư cá nhân.
    
    Returns:
        dict: Kết quả thực hiện.
    """
    try:
        if os.path.exists(PORTFOLIO_FILE):
            with open(PORTFOLIO_FILE, "w", encoding="utf-8") as f:
                json.dump([], f, indent=2, ensure_ascii=False)
        return {"status": "success", "message": "Đã xóa toàn bộ danh mục đầu tư hiện có."}
    except Exception as e:
        return {"status": "error", "message": str(e)}

import os
import json
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import vnstock as vs

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
    try:
        symbol = symbol.upper().strip()
        m = vs.Market()
        df = m.equity(symbol).quote()
        if df.empty:
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

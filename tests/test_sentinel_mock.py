import os
import sys
import json
import unittest
from unittest.mock import patch, MagicMock

# Thêm thư mục gốc vào python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import tools

class TestSentinelMock(unittest.TestCase):
    
    @patch('app.tools.get_portfolio')
    @patch('app.tools.get_stock_quote')
    @patch('app.tools.send_email_alert')
    def test_run_market_scan_with_trigger(self, mock_send_email, mock_get_quote, mock_get_portfolio):
        """Kiểm thử Sentinel kích hoạt cảnh báo thành công khi giá vượt ngưỡng."""
        # 1. Mock danh mục: FPT mua giá 65, ngưỡng cảnh báo 3%
        mock_get_portfolio.return_value = {
            "status": "success",
            "portfolio": [
                {
                    "symbol": "FPT",
                    "volume": 1000,
                    "cost_basis": 65.0,
                    "alert_threshold": 3.0
                }
            ]
        }
        
        # 2. Mock giá thị trường: FPT tăng lên 71.5 (Tăng 10.0% > ngưỡng 3.0%)
        mock_get_quote.return_value = {
            "status": "success",
            "quote": {
                "symbol": "FPT",
                "close_price": 71500 # đơn vị VNĐ
            }
        }
        
        # 3. Mock gửi email thành công
        mock_send_email.return_value = {
            "status": "success",
            "message": "Mock email sent successfully."
        }
        
        # Chạy hàm quét
        res = tools.run_market_scan()
        
        # Kiểm tra kết quả
        self.assertEqual(res["status"], "success")
        self.assertTrue(len(res["alerts"]) > 0)
        self.assertEqual(res["alerts"][0]["symbol"], "FPT")
        # Biến động: (71.5 - 65) / 65 * 100 = 10%
        self.assertAlmostEqual(res["alerts"][0]["diff_pct"], 10.0)
        
        # Kiểm tra xem hàm gửi email có được gọi đúng tiêu đề và nội dung
        mock_send_email.assert_called_once()
        args, kwargs = mock_send_email.call_args
        subject = args[0]
        body = args[1]
        self.assertIn("⚠️ CẢNH BÁO BIẾN ĐỘNG DANH MỤC TÀI CHÍNH", subject)
        self.assertIn("FPT", body)
        self.assertIn("+10.00%", body)
        
        print("\n✅ KIỂM THỬ MOCK THÀNH CÔNG: Cảnh báo biến động giá hoạt động chính xác!")
        print(f"Tiêu đề email đã soạn: {subject}")
        print(f"Nội dung email chứa dòng biến động: +10.00% (Giá vốn 65.00 -> Giá hiện tại 71.50)")

if __name__ == "__main__":
    unittest.main()

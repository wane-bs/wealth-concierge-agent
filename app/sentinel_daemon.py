import os
import time
import sys

# Thêm thư mục hiện tại và thư mục gốc vào python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.tools import run_market_scan

def main():
    # Nỗ lực tải dotenv để đọc tệp .env trong môi trường cục bộ
    try:
        from dotenv import load_dotenv
        # Tìm tệp .env ở cùng thư mục app/
        dotenv_path = os.path.join(os.path.dirname(__file__), ".env")
        if os.path.exists(dotenv_path):
            load_dotenv(dotenv_path)
        else:
            load_dotenv()
    except ImportError:
        pass
        
    interval_minutes = int(os.environ.get("SCAN_INTERVAL_MINUTES", "10"))
    interval_seconds = interval_minutes * 60

    print("="*60)
    print(f"BẮT ĐẦU CHẠY SENTINEL DAEMON (QUÉT ĐỊNH KỲ {interval_minutes} PHÚT/LẦN)")
    print("="*60)

    # Vòng lặp quét giá định kỳ
    while True:
        print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] Tiến hành quét giá danh mục định kỳ...")
        try:
            res = run_market_scan()
            print(f"Kết quả: {res.get('message', 'Không rõ kết quả')}")
        except Exception as e:
            print(f"Lỗi xảy ra trong quá trình quét: {e}")
        
        print(f"Đang chờ {interval_minutes} phút tiếp theo để thực hiện lượt quét tiếp theo...")
        time.sleep(interval_seconds)

if __name__ == "__main__":
    main()

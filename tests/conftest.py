import os
import sys
from dotenv import load_dotenv
from unittest.mock import MagicMock

# 1. Nạp các biến môi trường từ tệp app/.env trước khi chạy bất kỳ test case nào
dotenv_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "app", ".env")
if os.path.exists(dotenv_path):
    load_dotenv(dotenv_path)
else:
    load_dotenv()

# 2. Mock google.auth để tránh lỗi DefaultCredentialsError trên môi trường kiểm thử local
try:
    import google.auth
    google.auth.default = MagicMock(return_value=(MagicMock(), "mock-project-id"))
except ImportError:
    pass

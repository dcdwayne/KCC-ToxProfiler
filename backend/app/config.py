# 讀取根目錄 .env 的環境變數
import os
from pathlib import Path

from dotenv import load_dotenv
from sqlalchemy.engine import URL

# 以本檔案位置推算專案根目錄 (backend/app/config.py -> KCC-ToxProfiler/)
# 避免使用相對路徑 '../.env'，否則從不同工作目錄執行腳本時會找不到 .env
ROOT_DIR = Path(__file__).resolve().parents[2]
load_dotenv(ROOT_DIR / ".env")


def _require(name: str) -> str:
    """讀取必填環境變數，缺少時直接報錯，避免帶著 None 默默執行"""
    value = os.getenv(name)
    if not value:
        raise RuntimeError(f"缺少必要的環境變數 {name}，請檢查 {ROOT_DIR / '.env'}")
    return value


class Config:
    # database
    DB_USER = _require('DB_USER')
    DB_PASS = _require('DB_PASS')
    DB_HOST = os.getenv('DB_HOST', 'localhost')
    DB_PORT = int(os.getenv('DB_PORT', 5432))
    DB_NAME = _require('DB_NAME')

    # 使用 URL.create 組連線字串，密碼含 @ : / 等特殊字元時也能正確跳脫
    DATABASE_URL = URL.create(
        drivername="postgresql+psycopg2",
        username=DB_USER,
        password=DB_PASS,
        host=DB_HOST,
        port=DB_PORT,
        database=DB_NAME,
    )

    # authentication (JWT 金鑰不提供預設值，避免誤用不安全的金鑰)
    JWT_SECRET_KEY = _require('JWT_SECRET_KEY')
    ALGORITHM = os.getenv('ALGORITHM', 'HS256')
    ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv('ACCESS_TOKEN_EXPIRE_MINUTES', 30))
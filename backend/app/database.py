# SQLAlchemy 資料庫連線引擎與 Session 管理

# backend/app/database.py
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

from app.config import Config

# 帳號、密碼、Port 與資料庫名稱統一由根目錄 .env 提供 (與 docker-compose.yml 共用)
# 建立資料庫引擎
engine = create_engine(Config.DATABASE_URL, echo=False)

# 建立 Session 工廠，供後續 ETL 與 API 讀寫資料庫使用
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# 所有 ORM 資料表模型的基底類別
Base = declarative_base()
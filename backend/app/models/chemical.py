# backend/app/models/chemical.py
from sqlalchemy import Column, Integer, String, Boolean, DateTime
from sqlalchemy.sql import func
from app.database import Base

class TargetChemical(Base):
    __tablename__ = "target_chemicals"

    id = Column(Integer, primary_key=True, index=True)
    cas_number = Column(String(50), index=True, nullable=False)     # CAS 號碼 (允許重複，因為有多個名稱)
    chemical_name = Column(String(255), unique=True, index=True, nullable=False) # 搜尋用的化學名稱 (設為唯一，防止重複匯入)
    is_primary = Column(Boolean, default=False)                     # True 代表主名稱 (供前端顯示)，False 代表同義詞/別名
    created_at = Column(DateTime(timezone=True), server_default=func.now())
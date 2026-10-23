# backend/app/models/kcc.py
from sqlalchemy import Column, Integer, String, Text, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from pgvector.sqlalchemy import Vector
from app.database import Base

# ==========================================
# 第七張表：kcc_queries (KCC 關鍵片段資料表)
# ==========================================
class KccQuery(Base):
    __tablename__ = "kcc_queries"

    id = Column(Integer, primary_key=True, index=True)
    kcc_id = Column(String(10), index=True, nullable=False)        # 例如: "01", "02" ... "10" (對應前端 Dashboard)
    kcc_title = Column(String(100), nullable=False)                # 例如: "ELECTROPHILIC", "GENOTOXIC"
    query_code = Column(String(20), unique=True, index=True, nullable=False) # 例如: "KC1-1", "KC1-2" (唯一識別碼)
    query_text = Column(Text, nullable=False)                      # 完整的 KCC 關鍵片段英文描述
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # 一對一關聯到第八張表 (當關鍵片段文字修改或刪除時，連帶處理向量)
    embedding_record = relationship(
        "KccQueryEmbedding",
        back_populates="query",
        uselist=False,
        cascade="all, delete-orphan"
    )


# ==========================================
# 第八張表：kcc_query_embeddings (關鍵片段向量資料表)
# ==========================================
class KccQueryEmbedding(Base):
    __tablename__ = "kcc_query_embeddings"

    id = Column(Integer, primary_key=True, index=True)
    query_id = Column(Integer, ForeignKey("kcc_queries.id", ondelete="CASCADE"), unique=True, nullable=False)
    query_code = Column(String(20), unique=True, index=True, nullable=False) # 冗餘紀錄 KC1-1，方便在 pgAdmin 直接檢視
    
    # Voyage AI (voyage-3) 1024 維度向量
    embedding = Column(Vector(1024), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    query = relationship("KccQuery", back_populates="embedding_record")
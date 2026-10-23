# chunks 表 (paper_id 外鍵, chunk_text, embedding 向量)
# backend/app/models/chunk.py
from sqlalchemy import Column, Integer, String, Text, ForeignKey, DateTime, UniqueConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from pgvector.sqlalchemy import Vector
from app.database import Base

# ==========================================
# 第六張表：chunks (文獻摘要切片向量表)
# ==========================================
class PaperChunk(Base):
    __tablename__ = "chunks"

    id = Column(Integer, primary_key=True, index=True)
    paper_id = Column(Integer, ForeignKey("papers.id", ondelete="CASCADE"), nullable=False, index=True)
    pmid = Column(String(20), index=True, nullable=False)          # 冗餘紀錄 PMID，方便快速查詢
    
    chunk_index = Column(Integer, nullable=False)                  # 片段順序編號 (0, 1, 2...)，用於合併回原文
    char_start = Column(Integer, nullable=True)                    # 在原摘要中的起始字元索引
    char_end = Column(Integer, nullable=True)                      # 在原摘要中的結束字元索引
    chunk_text = Column(Text, nullable=False)                      # 切分後的片段文字
    
    # Voyage AI (voyage-3 / voyage-2) 標準向量維度為 1024 維
    embedding = Column(Vector(1024), nullable=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # 建立與 Paper 表的雙向關聯
    paper = relationship("Paper", backref="chunks")

    # 確保同一篇論文不會重複寫入相同編號的片段
    __table_args__ = (
        UniqueConstraint('paper_id', 'chunk_index', name='uix_paper_chunk_idx'),
    )
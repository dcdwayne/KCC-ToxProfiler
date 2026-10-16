# journal_rankings 表 (ISSN, Quartile, SJR)
# backend/app/models/journal.py
from sqlalchemy import Column, Integer, String, Float, Text
from app.database import Base

class JournalRanking(Base):
    __tablename__ = "journal_rankings"

    id = Column(Integer, primary_key=True, index=True)
    issn = Column(String(20), unique=True, index=True, nullable=False) # 清洗後的 8 碼純字串 ISSN (不含連字號)
    journal_title = Column(Text, nullable=False)                       # 期刊全名
    quartile = Column(String(10), index=True, nullable=False)          # Q1, Q2, Q3, Q4
    sjr_score = Column(Float, nullable=True)                           # SJR 分數
    h_index = Column(Integer, nullable=True)                           # H-Index
    ranking_year = Column(Integer, default=2025)                       # 排名年份
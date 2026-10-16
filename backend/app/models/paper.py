# papers 表 (PMID, Title, Abstract, ISSN, Q-Rank, Model_Type)
# backend/app/models/paper.py
from sqlalchemy import Column, Integer, String, Text, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base

# ==========================================
# 第三張表：papers (原始文獻表)
# ==========================================
class Paper(Base):
    __tablename__ = "papers"

    id = Column(Integer, primary_key=True, index=True)
    cas_number = Column(String(50), index=True, nullable=False)        # 對應表一的 CAS 號碼
    pmid = Column(String(20), unique=True, index=True, nullable=False) # PubMed 唯一 ID
    doi = Column(String(100), nullable=True)                           # DOI
    pmcid = Column(String(30), nullable=True)                          # PMCID (若有免費全文會有此 ID)
    
    article_title = Column(Text, nullable=False)                       # 論文標題
    journal_title = Column(Text, nullable=True)                        # 期刊完整名稱
    iso_abbreviation = Column(String(255), nullable=True)              # 期刊 ISO 縮寫
    abstract = Column(Text, nullable=False)                            # 完整摘要
    
    pub_date = Column(String(50), nullable=True)                       # 發表日期字串 (如 2024 Oct 12)
    pub_year = Column(Integer, index=True, nullable=True)              # 發表年份 (純數字，供前端年份過濾)
    pub_type = Column(Text, nullable=True)                             # 文章類型 (以分號串接，如 Journal Article; Review)
    
    issn = Column(String(20), nullable=True)                           # 期刊 ISSN (含紙本或電子)
    issn_linking = Column(String(20), nullable=True)                   # ISSN Linking
    
    # --- 衍生性欄位 ---
    citation_count = Column(Integer, default=0, index=True)            # 引用次數 (透過 ELink 批次計算)
    quartile = Column(String(15), default="Unranked", index=True)      # 期刊級別 (對照表二：Q1~Q4 或 Unranked)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # ORM 關聯設定 (刪除文獻時自動連帶刪除表四與表五的對應紀錄)
    model_info = relationship("PaperModel", back_populates="paper", uselist=False, cascade="all, delete-orphan")
    authors = relationship("PaperAuthor", back_populates="paper", cascade="all, delete-orphan")


# ==========================================
# 第四張表：paper_models (文獻實驗模型判斷資料表)
# ==========================================
class PaperModel(Base):
    __tablename__ = "paper_models"

    id = Column(Integer, primary_key=True, index=True)
    paper_id = Column(Integer, ForeignKey("papers.id", ondelete="CASCADE"), unique=True, nullable=False)
    pmid = Column(String(20), index=True, nullable=False)              # 對應文獻的 PMID
    
    model_category = Column(String(50), index=True, nullable=False)    # Human / In Vivo / In Vitro / Unknown
    base_score = Column(Integer, default=1, nullable=False)            # 證據權重分數：Human=10, In Vivo=7, In Vitro=3
    detection_source = Column(String(50), nullable=False)              # 判定來源：MeSH_Major / PubType / MeSH_Minor / Regex_Fallback
    matched_terms = Column(Text, nullable=True)                        # 實際命中的關鍵字或 MeSH 詞彙
    raw_mesh_terms = Column(Text, nullable=True)                       # 備份該篇論文所有 MeSH 詞彙 (供未來進階審查)

    paper = relationship("Paper", back_populates="model_info")


# ==========================================
# 第五張表：paper_authors (文獻作者資料表)
# ==========================================
class PaperAuthor(Base):
    __tablename__ = "paper_authors"

    id = Column(Integer, primary_key=True, index=True)
    paper_id = Column(Integer, ForeignKey("papers.id", ondelete="CASCADE"), nullable=False)
    pmid = Column(String(20), index=True, nullable=False)              # 對應文獻的 PMID
    
    author_order = Column(Integer, nullable=False)                     # 作者順序 (1 為第一作者)
    last_name = Column(String(100), nullable=True)                     # 姓氏 (LastName)
    fore_name = Column(String(100), nullable=True)                     # 名字 (ForeName)
    initials = Column(String(20), nullable=True)                       # 姓名縮寫 (Initials)
    affiliation = Column(Text, nullable=True)                          # 作者機構/單位 (Affiliation)

    paper = relationship("Paper", back_populates="authors")
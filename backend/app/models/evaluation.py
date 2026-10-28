# backend/app/models/evaluation.py
from sqlalchemy import Column, Integer, String, Float, Boolean, Text, ForeignKey, DateTime, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base

# ==========================================
# 第十張表：evaluations (評估主紀錄表)
# ==========================================
class Evaluation(Base):
    __tablename__ = "evaluations"

    id = Column(Integer, primary_key=True, index=True)
    cas_number = Column(String(50), index=True, nullable=False)        # 評估目標 CAS 號碼 (如 50-32-8)
    chemical_name = Column(String(255), nullable=False)                # 化學物質主顯示名稱 (如 Benzo[a]pyrene)
    
    # 紀錄使用者在首頁選定的初步篩選條件 (如 {"quartiles": ["Q1", "Q2"], "models": ["Human", "In Vivo"]})
    filter_criteria = Column(JSONB, nullable=True)
    
    # 狀態追蹤：REVIEWING (專家精鍊審查中) -> COMPLETED (已完成統合分析與報告生成)
    status = Column(String(30), default="REVIEWING", index=True, nullable=False)

    # 👇 新增：標記是否被選定為 FastMCP 查詢該化學物質時的代表評估紀錄 (同化學物質僅限一筆為 True)
    is_selected = Column(Boolean, default=False, index=True, nullable=False)
    
    # --- 以下欄位在專家按下『整合分析』按鈕後計算並寫入 ---
    hazard_score = Column(Integer, nullable=True)                      # 總體危害分數 (0 ~ 100)
    risk_level = Column(String(50), nullable=True)                     # HIGH RISK / MODERATE RISK / LOW RISK
    kcc_scores = Column(JSONB, nullable=True)                          # 儲存 10 個 KCC 個別分數與證據等級 (供 MetaDashboard 渲染)
    expert_report = Column(Text, nullable=True)                        # LLM 生成的專家版報告 (供 MetaExpert 渲染)
    public_report = Column(Text, nullable=True)                        # LLM 生成的大眾版報告 (供 MetaPublic 渲染)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # 一對多關聯：一筆評估主紀錄對應多筆證據池文獻明細
    evidences = relationship("EvaluationEvidence", back_populates="evaluation", cascade="all, delete-orphan")


# ==========================================
# 第九張表：evaluation_evidence (證據池明細表)
# ==========================================
class EvaluationEvidence(Base):
    __tablename__ = "evaluation_evidence"

    id = Column(Integer, primary_key=True, index=True)
    evaluation_id = Column(Integer, ForeignKey("evaluations.id", ondelete="CASCADE"), nullable=False, index=True)
    
    kcc_id = Column(String(10), index=True, nullable=False)            # 對應 "01" ~ "10"
    kcc_title = Column(String(100), nullable=False)                    # 對應 "ELECTROPHILIC" 等
    
    paper_id = Column(Integer, ForeignKey("papers.id", ondelete="CASCADE"), nullable=False, index=True)
    pmid = Column(String(20), index=True, nullable=False)              # 冗餘紀錄 PMID 方便查詢
    
    # --- 算分與篩選必備欄位 (直接存入快照，加速算分並支援未來專家手動微調) ---
    model_category = Column(String(50), nullable=False)                # Human / In Vivo / In Vitro / Unknown
    base_score = Column(Integer, nullable=False)                       # 10 / 7 / 3 / 1
    quartile = Column(String(15), nullable=False)                      # Q1 ~ Q4 / Unranked
    
    # --- RAG 檢索與重排適配度指標 ---
    best_query_code = Column(String(20), nullable=False)               # 該篇論文在此 KCC 配對分數最高的子查詢 (如 KC1-3)
    max_cosine_score = Column(Float, nullable=False, index=True)       # 第一階段：餘弦相似度最高分 (0~1)
    max_rerank_score = Column(Float, nullable=False, index=True)       # 第二階段：Cross-Encoder 重排最高分 (0~1)
    
    # 儲存該篇論文內部命中此 KCC 的所有切片明細 (供前端 Modal 標記螢光筆與 Hover 顯示對應 KCC 片段)
    # 格式: [{"chunk_index": 2, "query_code": "KC1-3", "query_text": "...", "cosine_score": 0.5769, "rerank_score": 0.82}]
    matched_chunks = Column(JSONB, nullable=False)
    
    # --- 專家精鍊控制欄位 ---
    # 預設為 True (納入統合分析)；當專家在 Systematic Review 頁面手動刪除文獻時，改為 False
    is_selected = Column(Boolean, default=True, index=True, nullable=False)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    evaluation = relationship("Evaluation", back_populates="evidences")
    paper = relationship("Paper")

    # 確保同一次評估中，同一個 KCC 底下不會重複出現同一篇論文
    __table_args__ = (
        UniqueConstraint('evaluation_id', 'kcc_id', 'paper_id', name='uix_eval_kcc_paper'),
    )
# backend/scripts/run_rag_evaluation.py
"""
現在我們寫一支測試腳本，直接針對你剛下載好的 Benzo[a]pyrene (50-32-8) 跑一次完整的 10 KCC 檢索與重排，把第九張表與第十張表建立並填滿資料！
"""

import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parent.parent))

from app.database import engine, SessionLocal, Base
from app.rag.retriever import build_evidence_pool_for_chemical

# 測試目標：苯駢芘 (Benzo[a]pyrene)
TARGET_CAS = "50-32-8"

def main():
    # 1. 自動在 PostgreSQL 中建立第九張表 (evaluation_evidence) 與第十張表 (evaluations)
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()

    try:
        # 2. 執行 10 KCC 檢索 + Cross-Encoder 重排
        eval_record = build_evidence_pool_for_chemical(
            db=db,
            cas_number=TARGET_CAS,
            quartiles=None,         # None 代表不限 Q1~Q4 全部檢索 (也可傳入 ["Q1", "Q2"])
            model_categories=None,  # None 代表不限模型 (也可傳入 ["Human", "In Vivo", "In Vitro"])
            min_cosine=0.38,        # Voyage-3 餘弦相似度門檻
            min_rerank=0.40,        # Voyage rerank-2 重排相關度門檻
            max_papers_per_kcc=15   # 每個 KCC 保留前 15 篇最相關的論文供專家審查
        )
        print(f"\n🚀 測試成功！請查看表十 (ID={eval_record.id}) 與表九的證據池明細！")
    finally:
        db.close()

if __name__ == "__main__":
    main()
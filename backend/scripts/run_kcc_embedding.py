# backend/scripts/run_kcc_embedding.py
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parent.parent))

from app.database import engine, SessionLocal, Base
from app.models.kcc import KccQuery, KccQueryEmbedding
from app.rag.embedder import embed_queries

def run_kcc_query_embedding():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()

    try:
        # 1. 找出表七中「還沒有在表八建立向量」的 KCC 關鍵片段
        embedded_query_ids = {r[0] for r in db.query(KccQueryEmbedding.query_id).all()}
        pending_queries = (
            db.query(KccQuery)
            .filter(~KccQuery.id.in_(embedded_query_ids) if embedded_query_ids else True)
            .order_by(KccQuery.id)
            .all()
        )

        if not pending_queries:
            print("✅ [表八: kcc_query_embeddings] 所有 KCC 關鍵片段皆已具備向量，無須重複計算！")
            return

        print(f"🚀 準備將 {len(pending_queries)} 條 KCC 關鍵片段透過 Voyage API (input_type='query') 轉為向量...")

        # 2. 由於 KCC 關鍵片段總數通常在 20~50 條左右，可一次批次送給 Voyage API
        texts = [q.query_text for q in pending_queries]
        embeddings = embed_queries(texts)

        # 3. 寫入第八張表
        for q_obj, emb in zip(pending_queries, embeddings):
            emb_record = KccQueryEmbedding(
                query_id=q_obj.id,
                query_code=q_obj.query_code,
                embedding=emb
            )
            db.add(emb_record)

        db.commit()
        print(f"🎉 [表八: kcc_query_embeddings] 寫入完成！共新增 {len(pending_queries)} 筆 1024 維 KCC 向量。")

    except Exception as e:
        db.rollback()
        print(f"❌ KCC 向量生成失敗：{e}")
        raise
    finally:
        db.close()

if __name__ == "__main__":
    run_kcc_query_embedding()
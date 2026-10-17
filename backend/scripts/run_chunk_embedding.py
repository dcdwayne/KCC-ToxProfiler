# backend/scripts/run_chunk_embedding.py
import sys
from pathlib import Path
from sqlalchemy import text

sys.path.append(str(Path(__file__).resolve().parent.parent))

from app.database import engine, SessionLocal, Base
from app.models import Paper, PaperChunk
from app.etl.splitter import split_abstract_into_chunks
from app.rag.embedder import embed_documents_batch

def run_chunking_and_embedding():
    db = SessionLocal()
    try:
        # 1. 確保 pgvector 擴充套件已啟用，並建立第六張表 chunks
        db.execute(text("CREATE EXTENSION IF NOT EXISTS vector;"))
        db.commit()
        Base.metadata.create_all(bind=engine)

        # 2. 找出尚未進行分片的文獻 (支援斷點續傳，已切過的不會重複花費 API 額度)
        processed_paper_ids = {r[0] for r in db.query(PaperChunk.paper_id).distinct().all()}
        unprocessed_papers = (
            db.query(Paper)
            .filter(~Paper.id.in_(processed_paper_ids) if processed_paper_ids else True)
            .all()
        )

        if not unprocessed_papers:
            print("✅ 所有文獻皆已完成分片與向量化，無須重複處理！")
            return

        print(f"📄 共有 {len(unprocessed_papers)} 篇文獻準備進行分片與 Voyage Embedding...")

        # 3. 執行句子分片
        pending_chunk_objs = []
        for paper in unprocessed_papers:
            chunk_dicts = split_abstract_into_chunks(paper.abstract)
            for c in chunk_dicts:
                pending_chunk_objs.append(
                    PaperChunk(
                        paper_id=paper.id,
                        pmid=paper.pmid,
                        chunk_index=c["chunk_index"],
                        char_start=c["char_start"],
                        char_end=c["char_end"],
                        chunk_text=c["chunk_text"]
                    )
                )

        print(f"✂️ 分片完成！共切出 {len(pending_chunk_objs)} 個完整語意片段 (平均每篇 {len(pending_chunk_objs)/len(unprocessed_papers):.1f} 片)。")

        # 4. 批次呼叫 Voyage API 生成 1024 維向量並寫入資料庫
        BATCH_SIZE = 64
        for start_idx in range(0, len(pending_chunk_objs), BATCH_SIZE):
            batch_objs = pending_chunk_objs[start_idx : start_idx + BATCH_SIZE]
            batch_texts = [obj.chunk_text for obj in batch_objs]

            print(f"   🚀 正在呼叫 Voyage API 轉換第 {start_idx + 1} ~ {start_idx + len(batch_objs)} 個片段...")
            embeddings = embed_documents_batch(batch_texts, batch_size=BATCH_SIZE)

            for obj, emb in zip(batch_objs, embeddings):
                obj.embedding = emb
                db.add(obj)

            # 每批立即 Commit 存檔，防止中途斷線浪費 API Token
            db.commit()

        # 5. 建立 pgvector HNSW 餘弦相似度索引 (讓未來的檢索速度達到毫秒級)
        print("⚡ 正在建立 pgvector HNSW 餘弦距離索引...")
        db.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_chunks_embedding_hnsw 
            ON chunks USING hnsw (embedding vector_cosine_ops);
        """))
        db.commit()

        print(f"🎉 大功告成！所有文獻片段與 1024 維向量已成功存入 [chunks] 資料表！")

    except Exception as e:
        db.rollback()
        print(f"❌ 執行失敗：{e}")
        raise
    finally:
        db.close()

if __name__ == "__main__":
    run_chunking_and_embedding()
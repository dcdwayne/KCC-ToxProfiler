# backend/scripts/run_chunk_embedding.py
"""
把原本的函式加上 cas_number: str | None = None 與 only_selected: bool = False 參數。這樣它既能從終端機單獨執行，也能直接被 FastAPI 的 search.py 呼叫（只切分並向量化這次篩選為 is_selected = True 的文獻）
"""
import sys
from pathlib import Path
from sqlalchemy import text
from sqlalchemy.orm import Session

sys.path.append(str(Path(__file__).resolve().parent.parent))

from app.database import engine, SessionLocal, Base
from app.models import Paper, PaperChunk
from app.etl.splitter import split_abstract_into_chunks
from app.rag.embedder import embed_documents_batch


def chunk_and_embed_papers(
    db: Session,
    cas_number: str | None = None,
    only_selected: bool = False
) -> int:
    """
    對符合條件且尚未切分向量的文獻進行 Chunking + Voyage Embedding。
    - 當 FastAPI 呼叫時，傳入 cas_number 與 only_selected=True，只處理使用者篩選出的文獻！
    """
    db.execute(text("CREATE EXTENSION IF NOT EXISTS vector;"))
    db.commit()
    Base.metadata.create_all(bind=engine)

    # 1. 找出已經切過片的 paper_id (已算過向量的文獻直接跳過，不重複扣 API 額度！)
    processed_paper_ids = {r[0] for r in db.query(PaperChunk.paper_id).distinct().all()}

    query = db.query(Paper)
    if cas_number:
        query = query.filter(Paper.cas_number == cas_number)
    if only_selected:
        query = query.filter(Paper.is_selected == True)
    if processed_paper_ids:
        query = query.filter(~Paper.id.in_(processed_paper_ids))

    unprocessed_papers = query.all()

    if not unprocessed_papers:
        print("✅ 所選範圍內的文獻皆已完成分片與向量化，無須重複呼叫 Voyage API！")
        return 0

    print(f"📄 共有 {len(unprocessed_papers)} 篇新入選文獻準備進行分片與 Voyage Embedding...")

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

    BATCH_SIZE = 64
    for start_idx in range(0, len(pending_chunk_objs), BATCH_SIZE):
        batch_objs = pending_chunk_objs[start_idx : start_idx + BATCH_SIZE]
        batch_texts = [obj.chunk_text for obj in batch_objs]

        print(f"   🚀 正在呼叫 Voyage API 轉換第 {start_idx + 1} ~ {start_idx + len(batch_objs)} 個片段...")
        embeddings = embed_documents_batch(batch_texts, batch_size=BATCH_SIZE)

        for obj, emb in zip(batch_objs, embeddings):
            obj.embedding = emb
            db.add(obj)

        db.commit()

    db.execute(text("""
        CREATE INDEX IF NOT EXISTS idx_chunks_embedding_hnsw 
        ON chunks USING hnsw (embedding vector_cosine_ops);
    """))
    db.commit()
    return len(pending_chunk_objs)


def run_chunking_and_embedding():
    db = SessionLocal()
    try:
        chunk_and_embed_papers(db, cas_number=None, only_selected=False)
    finally:
        db.close()


if __name__ == "__main__":
    run_chunking_and_embedding()
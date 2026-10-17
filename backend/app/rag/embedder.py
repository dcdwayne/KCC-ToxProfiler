# 呼叫 Embedding 模型將「文獻切片」與「KCC 關鍵片段」轉為向量
"""
Voyage AI 的重要特性：Voyage 的 API 支援 input_type 參數！當我們把**「文獻摘要片段」轉成向量存入資料庫時，要設定 input_type="document"；未來當我們把截圖中的「Query KCC 1-1」** 轉成向量去搜尋時，要設定 input_type="query"。這樣 Voyage 底層會針對「短問題找長文獻」進行非對稱優化，檢索準確度會大幅提升！
"""
# backend/app/rag/embedder.py
import os
import time
from pathlib import Path
from dotenv import load_dotenv
import voyageai

# 載入專案根目錄的 .env 檔案
ROOT_DIR = Path(__file__).resolve().parent.parent.parent.parent
load_dotenv(ROOT_DIR / ".env")

VOYAGE_API_KEY = os.getenv("VOYAGE_API_KEY")
# 使用 Voyage AI 主力 1024 維模型 voyage-3
VOYAGE_MODEL = "voyage-3"

def get_voyage_client() -> voyageai.Client:
    if not VOYAGE_API_KEY:
        raise ValueError("❌ 找不到 VOYAGE_API_KEY！請確認已在根目錄 .env 檔案中設定。")
    return voyageai.Client(api_key=VOYAGE_API_KEY)


def embed_documents_batch(texts: list[str], batch_size: int = 64) -> list[list[float]]:
    """
    將【文獻切片 (Chunks)】批次轉為 1024 維向量 (指定 input_type="document")
    Voyage API 單次最多支援 128 筆，這裡設 64 筆最穩定。
    """
    if not texts:
        return []

    vo = get_voyage_client()
    all_embeddings = []

    for i in range(0, len(texts), batch_size):
        batch = texts[i : i + batch_size]
        result = vo.embed(
            texts=batch,
            model=VOYAGE_MODEL,
            input_type="document"
        )
        all_embeddings.extend(result.embeddings)
        # 避免觸發免費版或初階 API 的 Rate Limit (RPM/TPM)
        time.sleep(0.3)

    return all_embeddings


def embed_queries(queries: list[str]) -> list[list[float]]:
    """
    將【KCC 關鍵字 (如 Query KCC 1-1 ~ 1-3)】轉為向量 (指定 input_type="query")
    供下一階段 RAG 餘弦相似度檢索使用！
    """
    if not queries:
        return []

    vo = get_voyage_client()
    result = vo.embed(
        texts=queries,
        model=VOYAGE_MODEL,
        input_type="query"
    )
    return result.embeddings
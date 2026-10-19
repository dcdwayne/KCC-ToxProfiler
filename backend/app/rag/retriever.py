# 建立 Retrieval + Rerank 檢索器
"""
這支檢索器是串聯表六、表七、表八、表九與表十的核心引擎。它的運作流程如下：
1.先在第十張表 (evaluations) 建立一筆狀態為 REVIEWING 的評估主紀錄。
2.依序針對 KC 01 到 KC 10 的每一組子關鍵字（如 KC1-1、KC1-2、KC1-3）：
- 第一階段（餘弦相似度召回）：在 PostgreSQL 中用 pgvector 找出屬於該化學物質、符合篩選條件、且餘弦相似度 >= min_cosine（預設設為 0.38）的前 25 個文獻片段。
- 第二階段（Cross-Encoder 重排）：將召回的片段送入 rerank-2 進行深度語意交叉評分，過濾出 rerank_score >= min_rerank（預設 0.40）的高品質片段。
- 第三階段（依論文歸納寫入表九）：將同一篇論文命中的多個片段整合成一筆 EvaluationEvidence 紀錄，把片段座標與對應的 KCx-y 存入 matched_chunks JSONB 欄位，並寫入第九張表 (evaluation_evidence)。
"""
# backend/app/rag/retriever.py
from collections import defaultdict
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.models import (
    TargetChemical, KccQuery, Evaluation, EvaluationEvidence
)
from app.rag.embedder import rerank_chunks


def build_evidence_pool_for_chemical(
    db: Session,
    cas_number: str,
    quartiles: list[str] | None = None,
    model_categories: list[str] | None = None,
    min_cosine: float = 0.38,
    recall_top_k_per_query: int = 25,
    min_rerank: float = 0.40,
    max_papers_per_kcc: int = 15
) -> Evaluation:
    """
    執行完整的 RAG 檢索 (Cosine Similarity) + 重排 (Cross-Encoder Rerank)，
    並將結果寫入第十張表 (evaluations) 與第九張表 (evaluation_evidence)。
    """
    # 1. 取得該 CAS 號碼的主顯示名稱
    chem = (
        db.query(TargetChemical)
        .filter_by(cas_number=cas_number, is_primary=True)
        .first()
    ) or db.query(TargetChemical).filter_by(cas_number=cas_number).first()

    chemical_name = chem.chemical_name if chem else cas_number

    # 2. 在【第十張表：evaluations】建立一筆新的評估任務紀錄
    new_eval = Evaluation(
        cas_number=cas_number,
        chemical_name=chemical_name,
        filter_criteria={
            "quartiles": quartiles,
            "model_categories": model_categories,
            "min_cosine": min_cosine,
            "min_rerank": min_rerank
        },
        status="REVIEWING"
    )
    db.add(new_eval)
    db.commit()
    db.refresh(new_eval)
    print(f"📋 已於 [表十: evaluations] 建立評估單 (ID: {new_eval.id}) | 目標: {chemical_name} ({cas_number})")

    # 3. 讀取【第七張表：kcc_queries】所有 KCC 關鍵片段，依 kcc_id (01~10) 分組
    all_kcc_queries = db.query(KccQuery).order_by(KccQuery.kcc_id, KccQuery.query_code).all()
    kcc_groups = defaultdict(list)
    for kq in all_kcc_queries:
        kcc_groups[(kq.kcc_id, kq.kcc_title)].append(kq)

    # 動態組合 SQL 過濾條件 (對應首頁的 Q1~Q4 與實驗模型篩選)
    extra_sql_filters = ""
    sql_params_base = {
        "cas_number": cas_number,
        "min_cosine": min_cosine,
        "top_k": recall_top_k_per_query
    }
    if quartiles:
        extra_sql_filters += " AND p.quartile = ANY(:quartiles)"
        sql_params_base["quartiles"] = quartiles
    if model_categories:
        extra_sql_filters += " AND m.model_category = ANY(:model_categories)"
        sql_params_base["model_categories"] = model_categories

    total_evidence_rows = 0

    # 4. 針對 10 個 KCC 依序執行「多查詢向量召回 + Cross-Encoder 重排」
    for (kcc_id, kcc_title), sub_queries in kcc_groups.items():
        print(f"🔎 正在檢索 KC {kcc_id} ({kcc_title}) - 共 {len(sub_queries)} 組子關鍵片段...")
        
        # 用來歸納同一篇論文在此 KCC 命中的所有切片: {paper_id: {...}}
        paper_hits = {}

        for sq in sub_queries:
            # --- 階段一：利用 pgvector 計算表八與表六的餘弦相似度 (Bi-Encoder Recall) ---
            recall_sql = text(f"""
                SELECT 
                    c.id AS chunk_id,
                    c.paper_id,
                    c.pmid,
                    c.chunk_index,
                    c.chunk_text,
                    p.quartile,
                    m.model_category,
                    m.base_score,
                    (1 - (c.embedding <=> ke.embedding)) AS cosine_score
                FROM chunks c
                JOIN papers p ON c.paper_id = p.id
                JOIN paper_models m ON p.id = m.paper_id
                CROSS JOIN kcc_query_embeddings ke
                WHERE p.cas_number = :cas_number
                  AND p.is_selected = TRUE
                  AND ke.query_code = :query_code
                  AND (1 - (c.embedding <=> ke.embedding)) >= :min_cosine
                  {extra_sql_filters}
                ORDER BY c.embedding <=> ke.embedding
                LIMIT :top_k;
            """)

            params = {**sql_params_base, "query_code": sq.query_code}
            candidates = db.execute(recall_sql, params).mappings().all()

            if not candidates:
                continue

            # --- 階段二：呼叫 Voyage Cross-Encoder (rerank-2) 進行重排 ---
            candidate_texts = [row["chunk_text"] for row in candidates]
            reranked_results = rerank_chunks(
                query_text=sq.query_text,
                chunk_texts=candidate_texts,
                top_k=len(candidate_texts)
            )

            # --- 階段三：過濾重排分數並歸納至母文獻 (Parent Paper) ---
            for rr in reranked_results:
                rerank_score = rr["relevance_score"]
                if rerank_score < min_rerank:
                    continue

                cand = candidates[rr["index"]]
                pid = cand["paper_id"]
                cos_score = round(float(cand["cosine_score"]), 4)
                rerank_score_rounded = round(float(rerank_score), 4)

                if pid not in paper_hits:
                    paper_hits[pid] = {
                        "paper_id": pid,
                        "pmid": cand["pmid"],
                        "model_category": cand["model_category"],
                        "base_score": cand["base_score"],
                        "quartile": cand["quartile"],
                        "best_query_code": sq.query_code,
                        "max_cosine_score": cos_score,
                        "max_rerank_score": rerank_score_rounded,
                        "matched_chunks": []
                    }
                else:
                    # 若同一篇論文被多個子查詢命中，更新最高分數與最佳子查詢代碼
                    if rerank_score_rounded > paper_hits[pid]["max_rerank_score"]:
                        paper_hits[pid]["max_rerank_score"] = rerank_score_rounded
                        paper_hits[pid]["best_query_code"] = sq.query_code
                    if cos_score > paper_hits[pid]["max_cosine_score"]:
                        paper_hits[pid]["max_cosine_score"] = cos_score

                # 記錄該切片命中的明細 (供前端 Modal 標記與 Hover 顯示)
                paper_hits[pid]["matched_chunks"].append({
                    "chunk_index": cand["chunk_index"],
                    "chunk_text": cand["chunk_text"], # 👈 補上這一行
                    "query_code": sq.query_code,
                    "query_text": sq.query_text,
                    "cosine_score": cos_score,
                    "rerank_score": rerank_score_rounded
                })

        # 5. 將該 KCC 命中的論文依 max_rerank_score 由高到低排序，取前 max_papers_per_kcc 篇寫入【第九張表】
        sorted_papers = sorted(
            paper_hits.values(),
            key=lambda x: (x["max_rerank_score"], x["max_cosine_score"]),
            reverse=True
        )[:max_papers_per_kcc]

        for p_data in sorted_papers:
            # 確保 matched_chunks 內部依 chunk_index 排序
            p_data["matched_chunks"].sort(key=lambda c: (c["chunk_index"], -c["rerank_score"]))
            
            evidence_obj = EvaluationEvidence(
                evaluation_id=new_eval.id,
                kcc_id=kcc_id,
                kcc_title=kcc_title,
                paper_id=p_data["paper_id"],
                pmid=p_data["pmid"],
                model_category=p_data["model_category"],
                base_score=p_data["base_score"],
                quartile=p_data["quartile"],
                best_query_code=p_data["best_query_code"],
                max_cosine_score=p_data["max_cosine_score"],
                max_rerank_score=p_data["max_rerank_score"],
                matched_chunks=p_data["matched_chunks"],
                is_selected=True
            )
            db.add(evidence_obj)
            total_evidence_rows += 1

        db.commit()
        print(f"   ✅ KC {kcc_id} 完成！共納入 {len(sorted_papers)} 篇高適配度文獻至證據池。")

    print(f"🎉 [表九: evaluation_evidence] 建置完成！評估單 #{new_eval.id} 共寫入 {total_evidence_rows} 筆 KCC 文獻證據。")
    return new_eval
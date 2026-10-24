# backend/app/routers/review.py
from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks
from pydantic import BaseModel
from sqlalchemy import func
from sqlalchemy.orm import Session
from concurrent.futures import ThreadPoolExecutor

from app.database import SessionLocal
from app.models import (
    Evaluation, EvaluationEvidence, Paper, PaperAuthor, PaperChunk, KccQuery
)
from app.rag.scorer import calculate_evaluation_scores
from app.rag.generator import generate_public_report, generate_expert_report

router = APIRouter(prefix="/api/review", tags=["Systematic Review"])


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# 資料庫實驗模型名稱 <-> 前端顯示名稱 對照
DB_TO_UI_MODEL = {
    "Human": "cohort",
    "In Vivo": "in vivo",
    "In Vitro": "in vitro",
    "Unknown": "unclassified"
}

UI_TO_DB_MODEL = {
    "cohort": "Human",
    "in vivo": "In Vivo",
    "in vitro": "In Vitro",
    "unclassified": "Unknown"
}

QUARTILE_SORT_ORDER = {"Q1": 1, "Q2": 2, "Q3": 3, "Q4": 4, "Unranked": 5}


# =====================================================================
# API 1: 取得評估單基本資訊與 10 個 KCC 的文獻數量及即時檢索狀態 (is_ready / is_processing)
# =====================================================================
@router.get("/{evaluation_id}/summary")
def get_review_summary(evaluation_id: int, db: Session = Depends(get_db)):
    eval_obj = db.query(Evaluation).filter_by(id=evaluation_id).first()
    if not eval_obj:
        raise HTTPException(status_code=404, detail=f"找不到評估單 ID: {evaluation_id}")

    # 取得標準 10 KCC 定義清單
    kcc_defs = (
        db.query(KccQuery.kcc_id, KccQuery.kcc_title)
        .distinct()
        .order_by(KccQuery.kcc_id)
        .all()
    )

    # 統計該評估單在各 KCC 中 is_selected = True 的文獻數
    counts_rows = (
        db.query(EvaluationEvidence.kcc_id, func.count(EvaluationEvidence.id))
        .filter(
            EvaluationEvidence.evaluation_id == evaluation_id,
            EvaluationEvidence.is_selected == True
        )
        .group_by(EvaluationEvidence.kcc_id)
        .all()
    )
    count_map = {kcc_id: cnt for kcc_id, cnt in counts_rows}

    # 判斷各 KCC 是否已由背景任務檢索完成
    criteria = eval_obj.filter_criteria or {}
    completed_kccs = set(criteria.get("completed_kccs", []))
    current_kcc = criteria.get("current_kcc")
    is_all_done = (eval_obj.status != "RETRIEVING")

    kcc_categories = []
    for k_id, k_title in kcc_defs:
        ready_flag = True if is_all_done else (k_id in completed_kccs)
        processing_flag = False if is_all_done else (current_kcc == k_id)
        kcc_categories.append({
            "id": k_id,
            "name": k_title,
            "count": count_map.get(k_id, 0),
            "is_ready": ready_flag,
            "is_processing": processing_flag
        })

    return {
        "evaluation_id": eval_obj.id,
        "cas_number": eval_obj.cas_number,
        "chemical_name": eval_obj.chemical_name,
        "status": eval_obj.status,
        "current_kcc": current_kcc,
        "completed_kcc_count": 10 if is_all_done else len(completed_kccs),
        "kcc_categories": kcc_categories
    }


# =====================================================================
# API 2: 取得特定 KCC 的相關文獻列表 (支援三種排序：資料來源、期刊排名、適配度)
# =====================================================================
@router.get("/{evaluation_id}/papers")
def get_kcc_papers(
    evaluation_id: int,
    kcc_name: str = Query(..., description="KCC 名稱，如 ELECTROPHILIC"),
    sort_by: str = Query("source", description="排序依據: source | quartile | rerank"),
    db: Session = Depends(get_db)
):
    rows = (
        db.query(EvaluationEvidence, Paper)
        .join(Paper, EvaluationEvidence.paper_id == Paper.id)
        .filter(
            EvaluationEvidence.evaluation_id == evaluation_id,
            EvaluationEvidence.kcc_title == kcc_name,
            EvaluationEvidence.is_selected == True
        )
        .all()
    )

    papers_list = []
    for ev, paper in rows:
        papers_list.append({
            "evidence_id": ev.id,
            "paper_id": paper.id,
            "pmid": paper.pmid,
            "title": paper.article_title,
            "model": DB_TO_UI_MODEL.get(ev.model_category, "unclassified"),
            "base_score": ev.base_score,
            "quartile": ev.quartile,
            "rerank_score": ev.max_rerank_score,
            "rerank_pct": round(ev.max_rerank_score * 100),  # 轉為整數百分比 (如 85%)
            "citations": paper.citation_count,
            "pub_year": paper.pub_year
        })

    # 排序邏輯
    if sort_by == "source":
        # 依資料來源權重排序 (cohort 10 > in vivo 7 > in vitro 3)，同分時依適配度排
        papers_list.sort(key=lambda x: (x["base_score"], x["rerank_score"]), reverse=True)
    elif sort_by == "quartile":
        # 依期刊排名排序 (Q1 > Q2 > Q3 > Q4 > Unranked)，同級時依適配度排
        papers_list.sort(key=lambda x: (QUARTILE_SORT_ORDER.get(x["quartile"], 99), -x["rerank_score"]))
    elif sort_by == "rerank":
        # 依適配度百分比由高到低排序
        papers_list.sort(key=lambda x: x["rerank_score"], reverse=True)

    return {
        "kcc_name": kcc_name,
        "total": len(papers_list),
        "papers": papers_list
    }


# =====================================================================
# API 3: 針對當前 KCC 執行『進階篩選』(將不符條件的文獻設為 is_selected = False)
# =====================================================================
class AdvancedFilterRequest(BaseModel):
    kcc_name: str
    models: list[str] = []          # 例如 ["cohort", "in vivo"]
    min_relevance_pct: float | None = None  # 適配度超過 X %
    start_year: int | None = None
    end_year: int | None = None
    min_citations: int | None = None
    journal_ranks: list[str] = []   # 例如 ["Q1", "Q2"]


@router.put("/{evaluation_id}/filter")
def filter_kcc_evidences(
    evaluation_id: int,
    payload: AdvancedFilterRequest,
    db: Session = Depends(get_db)
):
    rows = (
        db.query(EvaluationEvidence, Paper)
        .join(Paper, EvaluationEvidence.paper_id == Paper.id)
        .filter(
            EvaluationEvidence.evaluation_id == evaluation_id,
            EvaluationEvidence.kcc_title == payload.kcc_name,
            EvaluationEvidence.is_selected == True
        )
        .all()
    )

    allowed_db_models = [UI_TO_DB_MODEL[m.lower()] for m in payload.models if m.lower() in UI_TO_DB_MODEL]

    kept_count = 0
    for ev, paper in rows:
        keep = True

        # 1. 資料來源檢查
        if allowed_db_models and ev.model_category not in allowed_db_models:
            keep = False
        # 2. 適配度 (%) 檢查
        if keep and payload.min_relevance_pct is not None:
            if (ev.max_rerank_score * 100) <= payload.min_relevance_pct:
                keep = False
        # 3. 出版年份檢查
        if keep and payload.start_year is not None:
            if not paper.pub_year or paper.pub_year < payload.start_year:
                keep = False
        if keep and payload.end_year is not None:
            if not paper.pub_year or paper.pub_year > payload.end_year:
                keep = False
        # 4. 引用次數檢查 (超過 N 次)
        if keep and payload.min_citations is not None:
            if paper.citation_count <= payload.min_citations:
                keep = False
        # 5. 期刊排名檢查
        if keep and payload.journal_ranks:
            if ev.quartile not in payload.journal_ranks:
                keep = False

        if not keep:
            ev.is_selected = False
        else:
            kept_count += 1

    db.commit()
    return {
        "kcc_name": payload.kcc_name,
        "remaining_count": kept_count
    }


# =====================================================================
# API 4: 點擊『重新載入』按鈕，將該 KCC 下所有文獻重置回 is_selected = True
# =====================================================================
class ResetKccRequest(BaseModel):
    kcc_name: str


@router.put("/{evaluation_id}/reset")
def reset_kcc_evidences(
    evaluation_id: int,
    payload: ResetKccRequest,
    db: Session = Depends(get_db)
):
    updated_rows = (
        db.query(EvaluationEvidence)
        .filter(
            EvaluationEvidence.evaluation_id == evaluation_id,
            EvaluationEvidence.kcc_title == payload.kcc_name
        )
        .update({EvaluationEvidence.is_selected: True}, synchronize_session=False)
    )
    db.commit()

    return {
        "kcc_name": payload.kcc_name,
        "restored_count": updated_rows
    }


# =====================================================================
# API 5: 專家點擊單篇文獻右側的『X』手動刪除文獻 (is_selected = False)
# =====================================================================
@router.put("/{evaluation_id}/evidence/{evidence_id}/remove")
def remove_single_evidence(
    evaluation_id: int,
    evidence_id: int,
    db: Session = Depends(get_db)
):
    ev = (
        db.query(EvaluationEvidence)
        .filter_by(id=evidence_id, evaluation_id=evaluation_id)
        .first()
    )
    if not ev:
        raise HTTPException(status_code=404, detail="找不到該筆文獻證據紀錄")

    ev.is_selected = False
    db.commit()
    return {"message": "已從證據池移除", "evidence_id": evidence_id}


# =====================================================================
# API 6: 點擊文獻標題，取得彈出視窗 (PaperDetailModal.vue) 完整細節與 Hover 切片
# =====================================================================
@router.get("/{evaluation_id}/papers/{paper_id}/detail")
def get_paper_modal_detail(
    evaluation_id: int,
    paper_id: int,
    kcc_name: str = Query(..., description="當前檢視的 KCC 名稱"),
    db: Session = Depends(get_db)
):
    paper = db.query(Paper).filter_by(id=paper_id).first()
    if not paper:
        raise HTTPException(status_code=404, detail="找不到該篇文獻")

    ev = (
        db.query(EvaluationEvidence)
        .filter_by(evaluation_id=evaluation_id, paper_id=paper_id, kcc_title=kcc_name)
        .first()
    )

    # 1. 取得前三位主要作者與第一個機構單位 (Affiliation)
    authors_rows = (
        db.query(PaperAuthor)
        .filter_by(paper_id=paper.id)
        .order_by(PaperAuthor.author_order.asc())
        .limit(3)
        .all()
    )
    authors_list = []
    primary_affiliation = None
    for a in authors_rows:
        full_name = f"{a.fore_name or ''} {a.last_name or ''}".strip()
        if full_name:
            authors_list.append(full_name)
        if not primary_affiliation and a.affiliation:
            primary_affiliation = a.affiliation

    # 2. 整理文獻顯示類型標籤 (如 Review 或 Original Research)
    pub_type_raw = paper.pub_type or "Journal Article"
    if "Review" in pub_type_raw or "Meta-Analysis" in pub_type_raw:
        pub_type_badge = "Review"
    else:
        pub_type_badge = "Journal Article"

    # 3. 取得該文獻的所有摘要切片 (依 chunk_index 排序，拼回原文並標註命中之 KCC 關鍵片段)
    chunk_rows = (
        db.query(PaperChunk)
        .filter_by(paper_id=paper.id)
        .order_by(PaperChunk.chunk_index.asc())
        .all()
    )

    # 建立 chunk_index -> 命中的 KCC 關鍵片段清單映射
    matched_map = {}
    if ev and ev.matched_chunks:
        for m in ev.matched_chunks:
            c_idx = m.get("chunk_index")
            if c_idx not in matched_map:
                matched_map[c_idx] = []
            matched_map[c_idx].append({
                "kcc_code": m.get("query_code"),
                "query_text": m.get("query_text"),
                "cosine_score": m.get("cosine_score", 0),
                "rerank_score": m.get("rerank_score", 0)
            })

    chunks_payload = []
    if chunk_rows:
        for c in chunk_rows:
            chunks_payload.append({
                "chunk_index": c.chunk_index,
                "chunk_text": c.chunk_text,
                "matched_kccs": matched_map.get(c.chunk_index, [])
            })
    else:
        # 備援：若無切片則直接回傳完整摘要
        chunks_payload.append({
            "chunk_index": 0,
            "chunk_text": paper.abstract,
            "matched_kccs": []
        })

    return {
        "paper_id": paper.id,
        "pmid": paper.pmid,
        "title": paper.article_title,
        "pub_type": pub_type_badge,
        "pub_date": paper.pub_date,
        "authors": authors_list,
        "affiliation": primary_affiliation or "Affiliation information not listed in PubMed.",
        "model": DB_TO_UI_MODEL.get(ev.model_category, "unclassified") if ev else "unclassified",
        "quartile": ev.quartile if ev else paper.quartile,
        "citations": paper.citation_count,
        "rerank_pct": round(ev.max_rerank_score * 100) if ev else 0,
        "chunks": chunks_payload
    }


# 利用 Python 內建的 concurrent.futures.ThreadPoolExecutor 讓民眾版與專家版同時平行起跑（各自使用獨立的 SessionLocal() 確保資料庫執行緒安全）
def _task_public(evaluation_id: int):
    db = SessionLocal()
    try:
        generate_public_report(db, evaluation_id)
    except Exception as e:
        print(f"❌ 民眾版報告背景生成失敗 (Evaluation #{evaluation_id}): {e}")
    finally:
        db.close()

def _task_expert(evaluation_id: int):
    db = SessionLocal()
    try:
        generate_expert_report(db, evaluation_id)
    except Exception as e:
        print(f"❌ 專家版報告背景生成失敗 (Evaluation #{evaluation_id}): {e}")
    finally:
        db.close()

def _run_llm_reports_in_background(evaluation_id: int):
    """
    🚀 雙執行緒平行生成：
    同時向 Gemini 發出「民眾版」與「專家版」請求！
    民眾版因篇幅短會率先完成並解鎖前端按鈕，而專家版也在同一時間平行生成，總等待時間直接砍半！
    """
    with ThreadPoolExecutor(max_workers=2) as executor:
        executor.submit(_task_public, evaluation_id)
        executor.submit(_task_expert, evaluation_id)


# =====================================================================
# API 7: 點擊『執行統合分析』
# 1. 立即同步計算 10 KCC 與 Hazard Score (僅需 0.05 秒)
# 2. 將耗時的 LLM 報告生成交給 BackgroundTasks 在背景依序執行 (民眾版 -> 專家版)
# =====================================================================
@router.post("/{evaluation_id}/analyze")
def run_meta_analysis(
    evaluation_id: int,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    eval_obj = db.query(Evaluation).filter_by(id=evaluation_id).first()
    if not eval_obj:
        raise HTTPException(status_code=404, detail=f"找不到評估單 ID: {evaluation_id}")

    # 1. 先將舊報告清空並標記為 GENERATING_PUBLIC，讓前端知道民眾版正在生成中
    eval_obj.public_report = None
    eval_obj.expert_report = None
    eval_obj.status = "GENERATING_PUBLIC"
    db.commit()

    # 2. 立即計算 10 KCC 分數與總體危害分數 (瞬間完成)
    score_res = calculate_evaluation_scores(db, evaluation_id)

    # 3. 排入背景任務依序生成民眾版與專家版報告
    background_tasks.add_task(_run_llm_reports_in_background, evaluation_id)

    return {
        "message": "儀表板算分完成，LLM 報告已於背景啟動分段生成",
        "evaluation_id": evaluation_id,
        "hazard_score": score_res["hazard_score"],
        "risk_level": score_res["risk_level"],
        "status": "GENERATING_PUBLIC"
    }
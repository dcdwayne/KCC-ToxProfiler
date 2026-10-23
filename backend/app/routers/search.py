# backend/app/routers/search.py
from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks
from pydantic import BaseModel
from sqlalchemy import or_, not_
from sqlalchemy.orm import Session

from app.database import SessionLocal
from app.models import Paper, TargetChemical, Evaluation
from app.rag.retriever import build_evidence_pool_for_chemical
from scripts.run_chunk_embedding import chunk_and_embed_papers

router = APIRouter(prefix="/api/search", tags=["Preliminary Search"])

# 前端五個化學物質中文名稱與 CAS Number 的標準對照字典
CHEMICAL_NAME_TO_CAS = {
    "苯駢芘": ("50-32-8", "Benzo[a]pyrene"),
    "丙烯醯胺": ("79-06-1", "Acrylamide"),
    "塑化劑": ("117-81-7", "DEHP"),
    "戴奧辛": ("1746-01-6", "TCDD"),
    "全氟辛酸": ("335-67-1", "PFOA"),
}


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def resolve_chemical_cas(db: Session, chem_input: str) -> tuple[str, str]:
    """將前端傳入的中文名稱或英文名稱解析為 (cas_number, primary_english_name)"""
    if chem_input in CHEMICAL_NAME_TO_CAS:
        return CHEMICAL_NAME_TO_CAS[chem_input]

    # 若傳入的是英文名稱或 CAS 號，從表一 (target_chemicals) 查找
    rec = (
        db.query(TargetChemical)
        .filter(
            or_(
                TargetChemical.chemical_name.ilike(chem_input),
                TargetChemical.cas_number == chem_input
            )
        )
        .first()
    )
    if not rec:
        raise HTTPException(status_code=404, detail=f"找不到化學物質：{chem_input}")
    return rec.cas_number, rec.chemical_name


def apply_preliminary_filters(
    query,
    cas_number: str,
    start_year: int | None,
    end_year: int | None,
    min_citations: int | None,
    doc_type: str,
    journal_ranks: list[str]
):
    """
    核心過濾器：同時供 GET /preview 與 PUT /submit 共用，確保預覽篇數與實際入選篇數 100% 一致！
    """
    # 1. 化學物質 CAS 過濾
    query = query.filter(Paper.cas_number == cas_number)

    # 2. 出版年份區間過濾
    if start_year:
        query = query.filter(Paper.pub_year >= start_year)
    if end_year:
        query = query.filter(Paper.pub_year <= end_year)

    # 3. 引用次數過濾 (單選：至少被引用 N 次以上)
    if min_citations is not None and min_citations > 0:
        query = query.filter(Paper.citation_count >= min_citations)

    # 4. 文獻類型過濾 (嚴格依據 文獻分類.png 的 pub_type 判定邏輯)
    excluded_types = ["Editorial", "Letter", "Comment", "Published Erratum"]
    
    if doc_type == "Original Research":
        # 包含 Journal Article，但不包含 Review 及信件/社論/勘誤
        query = query.filter(Paper.pub_type.ilike("%Journal Article%"))
        query = query.filter(not_(Paper.pub_type.ilike("%Review%")))
        query = query.filter(not_(Paper.pub_type.ilike("%Meta-Analysis%")))
        for ex in excluded_types:
            query = query.filter(not_(Paper.pub_type.ilike(f"%{ex}%")))

    elif doc_type == "Review":
        # 包含 Review (含 Systematic Review) 或 Meta-Analysis
        query = query.filter(
            or_(
                Paper.pub_type.ilike("%Review%"),
                Paper.pub_type.ilike("%Meta-Analysis%")
            )
        )

    elif doc_type == "All":
        # 包含 Journal Article (Original Research + Review 的總和)，同樣排除勘誤/社論
        query = query.filter(
            or_(
                Paper.pub_type.ilike("%Journal Article%"),
                Paper.pub_type.ilike("%Review%"),
                Paper.pub_type.ilike("%Meta-Analysis%")
            )
        )
        for ex in excluded_types:
            query = query.filter(not_(Paper.pub_type.ilike(f"%{ex}%")))

    # 5. 期刊級別 (Q1~Q4) 多選過濾
    clean_ranks = [r.strip() for r in journal_ranks if r.strip()]
    if clean_ranks and "All" not in clean_ranks:
        query = query.filter(Paper.quartile.in_(clean_ranks))

    return query


# =====================================================================
# API 1: 點擊『初步篩選成果』取得符合條件的文獻篇數
# =====================================================================
@router.get("/preview")
def preview_filtered_papers(
    chemical: str = Query(..., description="選擇的化學物質名稱"),
    start_year: int = Query(2020),
    end_year: int = Query(2026),
    min_citations: int = Query(3),
    doc_type: str = Query("Original Research"),
    journal_ranks: str = Query("Q1,Q2", description="以逗號分隔的期刊級別，如 Q1,Q2 或 All"),
    db: Session = Depends(get_db)
):
    cas_number, eng_name = resolve_chemical_cas(db, chemical)
    ranks_list = journal_ranks.split(",") if journal_ranks else ["All"]

    base_query = db.query(Paper)
    filtered_query = apply_preliminary_filters(
        base_query, cas_number, start_year, end_year, min_citations, doc_type, ranks_list
    )

    count = filtered_query.count()
    return {
        "chemical_input": chemical,
        "chemical_name": eng_name,
        "cas_number": cas_number,
        "count": count
    }


# =====================================================================
# 背景執行任務：切片 + 向量化 + 10 KCC 逐一召回與重排
# =====================================================================
def _run_rag_pipeline_in_background(
    evaluation_id: int,
    cas_number: str,
    quartiles: list[str] | None
):
    bg_db = SessionLocal()
    try:
        # 1. 對尚未切分向量的入選文獻執行 Chunking & Embedding
        chunk_and_embed_papers(bg_db, cas_number=cas_number, only_selected=True)

        # 2. 依序針對 KC 01 ~ KC 10 執行餘弦相似度召回與 Cross-Encoder 重排
        build_evidence_pool_for_chemical(
            db=bg_db,
            cas_number=cas_number,
            quartiles=quartiles,
            model_categories=None,
            evaluation_id=evaluation_id
        )
    except Exception as e:
        print(f"❌ 背景執行 RAG 檢索與重排失敗 (Evaluation #{evaluation_id}): {e}")
        eval_obj = bg_db.query(Evaluation).filter_by(id=evaluation_id).first()
        if eval_obj:
            eval_obj.status = "REVIEWING"
            bg_db.commit()
    finally:
        bg_db.close()


# =====================================================================
# API 2: 點擊『確定送出篩選』
# 立即標記 papers.is_selected = True 並建立評估單，將 RAG 交給背景執行，讓前端瞬間跳轉！
# =====================================================================
class SubmitFilterRequest(BaseModel):
    chemical: str
    start_year: int = 2020
    end_year: int = 2026
    min_citations: int = 3
    doc_type: str = "Original Research"
    journal_ranks: list[str] = ["Q1", "Q2"]


@router.put("/submit")
def submit_filter_and_run_rag(
    payload: SubmitFilterRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    cas_number, eng_name = resolve_chemical_cas(db, payload.chemical)

    # 步驟 0: 先將該化學物質所有文獻的 is_selected 重置為 False
    db.query(Paper).filter(Paper.cas_number == cas_number).update(
        {Paper.is_selected: False}, synchronize_session=False
    )
    db.commit()

    # 步驟 1: 找出符合本次篩選條件的文獻 ID，將 is_selected 更新為 True
    filtered_query = apply_preliminary_filters(
        db.query(Paper.id),
        cas_number,
        payload.start_year,
        payload.end_year,
        payload.min_citations,
        payload.doc_type,
        payload.journal_ranks
    )
    selected_ids = [r[0] for r in filtered_query.all()]

    if not selected_ids:
        raise HTTPException(status_code=400, detail="目前篩選條件下沒有符合的文獻 (0 篇)，請放寬篩選條件！")

    db.query(Paper).filter(Paper.id.in_(selected_ids)).update(
        {Paper.is_selected: True}, synchronize_session=False
    )
    db.commit()
    print(f"✅ 已將 {eng_name} ({cas_number}) 共 {len(selected_ids)} 篇文獻標記為 is_selected = True！")

    # 步驟 2: 立即在【第十張表：evaluations】建立一筆 status="RETRIEVING" 的評估單
    new_eval = Evaluation(
        cas_number=cas_number,
        chemical_name=eng_name,
        filter_criteria={
            "chemical_zh": payload.chemical,
            "start_year": payload.start_year,
            "end_year": payload.end_year,
            "min_citations": payload.min_citations,
            "doc_type": payload.doc_type,
            "journal_ranks": payload.journal_ranks,
            "selected_paper_count": len(selected_ids),
            "completed_kccs": [],
            "current_kcc": "CHUNKING"
        },
        status="RETRIEVING"
    )
    db.add(new_eval)
    db.commit()
    db.refresh(new_eval)

    # 步驟 3: 將耗時的 Chunking + Embedding + 10 KCC 重排排入背景任務
    quartiles_filter = None if "All" in payload.journal_ranks else payload.journal_ranks
    background_tasks.add_task(
        _run_rag_pipeline_in_background,
        new_eval.id,
        cas_number,
        quartiles_filter
    )

    return {
        "message": "初步篩選已送出，正在背景建立 10 KCC 證據池",
        "evaluation_id": new_eval.id,
        "cas_number": cas_number,
        "chemical_name": eng_name,
        "selected_paper_count": len(selected_ids),
        "status": "RETRIEVING"
    }
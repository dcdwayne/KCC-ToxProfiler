# backend/app/routers/history.py
from datetime import timezone, timedelta
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.database import SessionLocal
from app.models import Evaluation, EvaluationEvidence

router = APIRouter(prefix="/api/history", tags=["Historical Records"])

# 台灣標準時間 (UTC+8)
TW_TZ = timezone(timedelta(hours=8))

# 狀態排序優先級 (COMPLETED 排最前)
STATUS_SORT_ORDER = {
    "COMPLETED": 1,
    "GENERATING_EXPERT": 2,
    "GENERATING_PUBLIC": 3,
    "GENERATING_REPORTS": 4,
    "REVIEWING": 5,
    "RETRIEVING": 6
}


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def format_to_taiwan_time(dt) -> str:
    """將資料庫時間轉為台灣時區 (UTC+8) 並格式化為 YYYY-MM-DD HH:MM:SS"""
    if not dt:
        return "--"
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    tw_dt = dt.astimezone(TW_TZ)
    return tw_dt.strftime("%Y-%m-%d %H:%M:%S")


def _get_record_lang(r: Evaluation) -> str:
    """從 filter_criteria JSONB 判斷該筆紀錄為中文 ('zh') 或英文 ('en')"""
    criteria = r.filter_criteria or {}
    return "en" if criteria.get("lang") == "en" else "zh"


# =====================================================================
# API 1: 取得所有歷史評估紀錄 (支援多選組合排序：含評估時間由近到遠)
# =====================================================================
@router.get("")
def get_history_records(
    sort_by: str = Query("", description="多選排序欄位，以逗號分隔，如: chemical,hazard,status,time"),
    db: Session = Depends(get_db)
):
    records = db.query(Evaluation).order_by(Evaluation.id.desc()).all()

    items = []
    for r in records:
        items.append({
            "id": r.id,
            "cas_number": r.cas_number,
            "chemical_name": (r.chemical_name or r.cas_number).upper(),
            "hazard_score": r.hazard_score,
            "risk_level": r.risk_level or "UNSCORED",
            "status": r.status or "REVIEWING",
            "report_lang": _get_record_lang(r),
            "is_selected": bool(r.is_selected),
            "created_at_tw": format_to_taiwan_time(r.created_at),
            "raw_timestamp": r.created_at.timestamp() if r.created_at else 0
        })

    # 處理多選排序 (依照前端點擊放入的順序作為主次排序權重)
    sort_fields = [s.strip() for s in sort_by.split(",") if s.strip()]
    if sort_fields:
        def multi_sort_key(item):
            key_tuple = []
            for field in sort_fields:
                if field == "chemical":
                    # 依化學物質英文字母 A -> Z
                    key_tuple.append(item["chemical_name"])
                elif field == "hazard":
                    # 依危害分數由高到低 (未算分者排最後)
                    score = item["hazard_score"] if item["hazard_score"] is not None else -1
                    key_tuple.append(-score)
                elif field == "status":
                    # 依完成狀態優先級 (COMPLETED 最優先)
                    key_tuple.append(STATUS_SORT_ORDER.get(item["status"], 99))
                elif field == "time":
                    # 依評估時間由近到遠 (Timestamp 越大代表越新，加負號由大排到小)
                    key_tuple.append(-item["raw_timestamp"])
            # 預設最終以最新 ID 排前面
            key_tuple.append(-item["id"])
            return tuple(key_tuple)

        items.sort(key=multi_sort_key)

    return {
        "total": len(items),
        "records": items
    }


# =====================================================================
# API 2: 切換勾選狀態 (同一個化學物質在「中文版 (zh)」與「英文版 (en)」各限勾選一筆作為 FastMCP 資料源)
# =====================================================================
class ToggleSelectRequest(BaseModel):
    is_selected: bool


@router.put("/{evaluation_id}/select")
def toggle_select_record(
    evaluation_id: int,
    payload: ToggleSelectRequest,
    db: Session = Depends(get_db)
):
    target = db.query(Evaluation).filter_by(id=evaluation_id).first()
    if not target:
        raise HTTPException(status_code=404, detail=f"找不到評估紀錄 ID: {evaluation_id}")

    target_lang = _get_record_lang(target)

    # 若勾選為 True，僅將「同一個 cas_number 且同一個語系 (zh 或 en)」的其他紀錄取消勾選
    if payload.is_selected:
        same_chem_rows = (
            db.query(Evaluation)
            .filter(
                Evaluation.cas_number == target.cas_number,
                Evaluation.id != evaluation_id,
                Evaluation.is_selected == True
            )
            .all()
        )
        for row in same_chem_rows:
            if _get_record_lang(row) == target_lang:
                row.is_selected = False

    target.is_selected = payload.is_selected
    db.commit()

    return {
        "evaluation_id": target.id,
        "cas_number": target.cas_number,
        "chemical_name": target.chemical_name,
        "report_lang": target_lang,
        "is_selected": target.is_selected
    }


# =====================================================================
# API 3: 刪除單筆評估紀錄 (同步刪除 evaluation_evidence 與 evaluations)
# =====================================================================
@router.delete("/{evaluation_id}")
def delete_evaluation_record(evaluation_id: int, db: Session = Depends(get_db)):
    target = db.query(Evaluation).filter_by(id=evaluation_id).first()
    if not target:
        raise HTTPException(status_code=404, detail=f"找不到評估紀錄 ID: {evaluation_id}")

    # 1. 先刪除表九 (evaluation_evidence) 中所有指定 evaluation_id 的紀錄
    deleted_evidences = (
        db.query(EvaluationEvidence)
        .filter(EvaluationEvidence.evaluation_id == evaluation_id)
        .delete(synchronize_session=False)
    )

    # 2. 再刪除表十 (evaluations) 該筆評估紀錄
    db.delete(target)
    db.commit()

    return {
        "message": "評估紀錄與關聯證據已成功刪除",
        "deleted_evaluation_id": evaluation_id,
        "deleted_evidence_count": deleted_evidences
    }
# backend/app/routers/admin.py
from datetime import datetime, timezone, timedelta
from fastapi import APIRouter, Depends, HTTPException, Query, Request
from pydantic import BaseModel
from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.database import SessionLocal
from app.models.user import User, UserLoginLog

router = APIRouter(prefix="/api/admin", tags=["Account & RBAC Management"])

# 台灣標準時間 (UTC+8)
TW_TZ = timezone(timedelta(hours=8))


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def format_to_taiwan_time(dt: datetime | None) -> str | None:
    """將資料庫時間轉換為台灣時區 (UTC+8) 字串 YYYY-MM-DD HH:MM:SS"""
    if not dt:
        return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(TW_TZ).strftime("%Y-%m-%d %H:%M:%S")


def require_system_admin(request: Request, db: Session = Depends(get_db)) -> User:
    """後端 RBAC 守衛：強制驗證當前 Session 是否為有效之『系統管理者』"""
    session_user = request.session.get("user")
    if not session_user or not session_user.get("id"):
        raise HTTPException(status_code=401, detail="請先登入系統管理者帳號")

    admin_user = db.query(User).filter_by(id=session_user["id"]).first()
    if (
        not admin_user
        or admin_user.role != "系統管理者"
        or admin_user.account_status != "ACTIVE"
        or admin_user.approval_status != "APPROVED"
    ):
        raise HTTPException(status_code=403, detail="權限不足：此頁面僅開放『系統管理者』存取")

    return admin_user


# =====================================================================
# API 1: 查詢所有註冊帳號與權限核准清單 (支援多條件篩選)
# =====================================================================
@router.get("/users")
def list_users_for_approval(
    keyword: str = Query("", description="搜尋信箱、姓名或單位"),
    role: str = Query("ALL", description="篩選角色：ALL | 系統管理者 | 專家 | 會員"),
    approval_status: str = Query("ALL", description="篩選確認狀態：ALL | PENDING | APPROVED | REJECTED"),
    account_status: str = Query("ALL", description="篩選帳號狀態：ALL | ACTIVE | DISABLED"),
    db: Session = Depends(get_db),
    current_admin: User = Depends(require_system_admin)
):
    query = db.query(User)

    # 1. 關鍵字過濾 (信箱 / 姓名 / 單位 / 職稱)
    kw = keyword.strip()
    if kw:
        query = query.filter(
            or_(
                User.email.ilike(f"%{kw}%"),
                User.name.ilike(f"%{kw}%"),
                User.organization.ilike(f"%{kw}%"),
                User.job_title.ilike(f"%{kw}%")
            )
        )

    # 2. 權限角色過濾
    if role and role != "ALL":
        query = query.filter(User.role == role)

    # 3. 確認狀態過濾 (PENDING 待審核 / APPROVED 已通過 / REJECTED 未通過)
    if approval_status and approval_status != "ALL":
        query = query.filter(User.approval_status == approval_status)

    # 4. 帳號狀態過濾 (ACTIVE 啟用 / DISABLED 停用)
    if account_status and account_status != "ALL":
        query = query.filter(User.account_status == account_status)

    # 統計各狀態數量供前端頂部バッジ顯示
    pending_count = db.query(User).filter(User.approval_status == "PENDING").count()

    # 預設讓「待審核 (PENDING)」排最前面，其次依 ID 由新到舊排序
    users = query.order_by(User.id.desc()).all()

    items = []
    for u in users:
        # 只有已審核 (APPROVED 或 REJECTED) 的紀錄才回傳核定時間
        is_audited = u.approval_status in ("APPROVED", "REJECTED")
        approved_time_str = format_to_taiwan_time(u.approved_at) if is_audited else None

        items.append({
            "id": u.id,
            "email": u.email,
            "name": u.name or "--",
            "organization": u.organization or "--",
            "job_title": u.job_title or "--",
            "phone": u.phone or "--",
            "role": u.role,
            "approval_status": u.approval_status,
            "account_status": u.account_status,
            "login_count": u.login_count or 0,
            "approved_at_tw": approved_time_str,
            "created_at_tw": format_to_taiwan_time(u.created_at) or "--",
            "is_self": (u.id == current_admin.id)
        })

    # 將 PENDING 待審核項目置頂，方便管理員第一時間處理
    items.sort(key=lambda x: (0 if x["approval_status"] == "PENDING" else 1, -x["id"]))

    return {
        "total": len(items),
        "pending_total": pending_count,
        "users": items
    }


# =====================================================================
# API 2: 審核帳號、變更權限角色或切換帳號啟停狀態
# =====================================================================
class UpdateUserPermissionRequest(BaseModel):
    role: str | None = None              # '系統管理者' | '專家' | '會員'
    approval_status: str | None = None   # 'PENDING' | 'APPROVED' | 'REJECTED'
    account_status: str | None = None    # 'ACTIVE' | 'DISABLED'


@router.put("/users/{user_id}")
def update_user_permission(
    user_id: int,
    payload: UpdateUserPermissionRequest,
    db: Session = Depends(get_db),
    current_admin: User = Depends(require_system_admin)
):
    target = db.query(User).filter_by(id=user_id).first()
    if not target:
        raise HTTPException(status_code=404, detail=f"找不到使用者 ID: {user_id}")

    # 安全防呆：禁止系統管理者將「自己」停權、退回待審核或降級角色
    if target.id == current_admin.id:
        if payload.account_status and payload.account_status != "ACTIVE":
            raise HTTPException(status_code=400, detail="安全限制：無法將您目前登入的管理員帳號設為停用！")
        if payload.approval_status and payload.approval_status != "APPROVED":
            raise HTTPException(status_code=400, detail="安全限制：無法取消您目前登入的管理員核准狀態！")
        if payload.role and payload.role != "系統管理者":
            raise HTTPException(status_code=400, detail="安全限制：無法調降您目前登入的系統管理者角色！")

    # 1. 更新權限角色
    if payload.role is not None:
        if payload.role not in ("系統管理者", "專家", "會員"):
            raise HTTPException(status_code=400, detail="無效的權限角色名稱")
        target.role = payload.role

    # 2. 更新確認狀態 (審核狀態) 與核定時間
    if payload.approval_status is not None:
        if payload.approval_status not in ("PENDING", "APPROVED", "REJECTED"):
            raise HTTPException(status_code=400, detail="無效的確認狀態代碼")
        target.approval_status = payload.approval_status

        # 規則：已審核 (通過/未通過) 紀錄當下核定時間；若改回待審核則清空核定時間
        if payload.approval_status in ("APPROVED", "REJECTED"):
            target.approved_at = datetime.now(timezone.utc)
        else:
            target.approved_at = None

    # 3. 更新帳號啟停狀態
    if payload.account_status is not None:
        if payload.account_status not in ("ACTIVE", "DISABLED"):
            raise HTTPException(status_code=400, detail="無效的帳號狀態代碼")
        target.account_status = payload.account_status

    db.commit()
    db.refresh(target)

    is_audited = target.approval_status in ("APPROVED", "REJECTED")
    return {
        "message": "帳號權限設定已更新",
        "user": {
            "id": target.id,
            "email": target.email,
            "role": target.role,
            "approval_status": target.approval_status,
            "account_status": target.account_status,
            "approved_at_tw": format_to_taiwan_time(target.approved_at) if is_audited else None
        }
    }


# =====================================================================
# API 3: 查詢使用者登入紀錄 Log (支援台灣時區時間區間查詢與多條件過濾)
# =====================================================================
@router.get("/logs")
def list_user_login_logs(
    start_date: str = Query("", description="開始日期 YYYY-MM-DD (台灣時區)"),
    end_date: str = Query("", description="結束日期 YYYY-MM-DD (台灣時區)"),
    keyword: str = Query("", description="搜尋信箱、姓名或來源 IP"),
    role: str = Query("ALL", description="篩選角色：ALL | 系統管理者 | 專家 | 會員 | 訪客"),
    login_result: str = Query("ALL", description="篩選結果：ALL | SUCCESS | GUEST | FAILED_PWD | FAILED_PENDING | FAILED_REJECTED | FAILED_DISABLED"),
    db: Session = Depends(get_db),
    current_admin: User = Depends(require_system_admin)
):
    query = db.query(UserLoginLog)

    # 1. 台灣時區 (UTC+8) 時間區間過濾
    if start_date.strip():
        try:
            start_dt_tw = datetime.strptime(start_date.strip(), "%Y-%m-%d").replace(
                hour=0, minute=0, second=0, microsecond=0, tzinfo=TW_TZ
            )
            query = query.filter(UserLoginLog.login_at >= start_dt_tw.astimezone(timezone.utc))
        except ValueError:
            raise HTTPException(status_code=400, detail="開始日期格式錯誤，請使用 YYYY-MM-DD")

    if end_date.strip():
        try:
            end_dt_tw = datetime.strptime(end_date.strip(), "%Y-%m-%d").replace(
                hour=23, minute=59, second=59, microsecond=999999, tzinfo=TW_TZ
            )
            query = query.filter(UserLoginLog.login_at <= end_dt_tw.astimezone(timezone.utc))
        except ValueError:
            raise HTTPException(status_code=400, detail="結束日期格式錯誤，請使用 YYYY-MM-DD")

    # 2. 關鍵字過濾 (信箱 / 姓名 / IP)
    kw = keyword.strip()
    if kw:
        query = query.filter(
            or_(
                UserLoginLog.email.ilike(f"%{kw}%"),
                UserLoginLog.name.ilike(f"%{kw}%"),
                UserLoginLog.ip_address.ilike(f"%{kw}%")
            )
        )

    # 3. 角色過濾
    if role and role != "ALL":
        query = query.filter(UserLoginLog.role == role)

    # 4. 登入結果過濾
    if login_result and login_result != "ALL":
        query = query.filter(UserLoginLog.login_result == login_result)

    logs = query.order_by(UserLoginLog.login_at.desc(), UserLoginLog.id.desc()).limit(1000).all()

    items = []
    for lg in logs:
        items.append({
            "id": lg.id,
            "user_id": lg.user_id,
            "email": lg.email,
            "name": lg.name or "--",
            "role": lg.role,
            "login_result": lg.login_result,
            "ip_address": lg.ip_address or "--",
            "login_at_tw": format_to_taiwan_time(lg.login_at) or "--"
        })

    return {
        "total": len(items),
        "logs": items
    }
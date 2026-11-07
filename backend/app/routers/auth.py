# backend/app/routers/auth.py
import os
import re
import hashlib
import secrets
from datetime import datetime, timezone, timedelta
from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, field_validator
from sqlalchemy.orm import Session

from app.database import SessionLocal
from app.models.user import User, UserLoginLog

router = APIRouter(prefix="/api/auth", tags=["Authentication & RBAC"])

TW_TZ = timezone(timedelta(hours=8))

# 嚴格電子信箱 Regex 格式驗證
EMAIL_REGEX = re.compile(r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$")


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# =====================================================================
# 密碼雜湊與驗證工具 (使用 Python 內建 PBKDF2-HMAC-SHA256，零外部相依衝突)
# =====================================================================
def hash_password(password: str) -> str:
    salt = secrets.token_hex(16)
    pwd_hash = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt.encode("utf-8"), 100000).hex()
    return f"{salt}${pwd_hash}"


def verify_password(plain_password: str, stored_hash: str) -> bool:
    if not stored_hash or "$" not in stored_hash:
        return False
    salt, pwd_hash = stored_hash.split("$", 1)
    check_hash = hashlib.pbkdf2_hmac("sha256", plain_password.encode("utf-8"), salt.encode("utf-8"), 100000).hex()
    return secrets.compare_digest(pwd_hash, check_hash)


# =====================================================================
# 防範 Indirect Prompt Injection 與 XSS 的輸入清洗器
# =====================================================================
def sanitize_user_field(val: str | None, max_len: int = 50) -> str | None:
    if not val:
        return None
    # 移除換行、控制字元、Markdown 標題井字號、HTML 尖括號與特殊括號
    cleaned = re.sub(r"[\r\n\t#<>\[\]{}【】`]", "", val).strip()
    return cleaned[:max_len] if cleaned else None


def get_client_ip(request: Request) -> str:
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        return forwarded.split(",")[0].strip()
    real_ip = request.headers.get("x-real-ip")
    if real_ip:
        return real_ip.strip()
    return request.client.host if request.client else "127.0.0.1"


# =====================================================================
# 系統啟動時自動建立「種子系統管理者」帳號 (Bootstrap Admin)
# =====================================================================
def ensure_initial_admin():
    db = SessionLocal()
    try:
        admin_email = os.getenv("INIT_ADMIN_EMAIL", "admin@toxprofiler.com").lower().strip()
        admin_pwd = os.getenv("INIT_ADMIN_PASSWORD", "Admin1234!")

        existing = db.query(User).filter(User.email == admin_email).first()
        if not existing:
            seed_admin = User(
                email=admin_email,
                password_hash=hash_password(admin_pwd),
                name="系統最高管理員",
                organization="KCC ToxProfiler 核心團隊",
                job_title="System Administrator",
                role="系統管理者",
                approval_status="APPROVED",
                account_status="ACTIVE",
                approved_at=datetime.now(timezone.utc)
            )
            db.add(seed_admin)
            db.commit()
            print(f"👑 已自動建立初始『系統管理者』帳號：{admin_email} (預設密碼：{admin_pwd})")
    except Exception as e:
        print(f"⚠️ 初始化管理員檢查略過: {e}")
    finally:
        db.close()


# =====================================================================
# API 1: 取得目前 Session 登入狀態 (GET /api/auth/me)
# =====================================================================
@router.get("/me")
def get_current_session_user(request: Request, db: Session = Depends(get_db)):
    session_user = request.session.get("user")
    if not session_user:
        return {
            "is_authenticated": False,
            "is_guest": False,
            "user": None
        }

    # 若為訪客模式
    if session_user.get("role") == "訪客":
        return {
            "is_authenticated": False,
            "is_guest": True,
            "user": session_user
        }

    # 雙重確認資料庫內的最新狀態 (若被管理員停權或改角色，立即同步生效！)
    db_user = db.query(User).filter_by(id=session_user.get("id")).first()
    if not db_user or db_user.account_status != "ACTIVE" or db_user.approval_status != "APPROVED":
        request.session.clear()
        return {
            "is_authenticated": False,
            "is_guest": False,
            "user": None
        }

    updated_session = {
        "id": db_user.id,
        "email": db_user.email,
        "name": db_user.name or db_user.email.split("@")[0],
        "role": db_user.role,
        "organization": db_user.organization
    }
    request.session["user"] = updated_session

    return {
        "is_authenticated": True,
        "is_guest": False,
        "user": updated_session
    }


# =====================================================================
# API 2: 帳號密碼登入 (POST /api/auth/login)
# =====================================================================
class LoginRequest(BaseModel):
    email: str
    password: str

    @field_validator("email")
    @classmethod
    def validate_email_format(cls, v: str) -> str:
        clean_email = v.strip().lower()
        if not EMAIL_REGEX.match(clean_email):
            raise ValueError("請輸入有效的電子信箱格式（例如：user@example.com）")
        return clean_email


@router.post("/login")
def login_user(payload: LoginRequest, request: Request, db: Session = Depends(get_db)):
    ip = get_client_ip(request)
    user = db.query(User).filter(User.email == payload.email).first()

    # 1. 帳號不存在或密碼錯誤
    if not user or not verify_password(payload.password, user.password_hash):
        db.add(UserLoginLog(
            user_id=user.id if user else None,
            email=payload.email,
            name=user.name if user else "未知使用者",
            role=user.role if user else "未知",
            login_result="FAILED_PWD",
            ip_address=ip
        ))
        db.commit()
        raise HTTPException(status_code=401, detail="帳號或密碼輸入錯誤，請重新確認！")

    # 2. 檢查確認狀態 (待審核 / 未通過)
    if user.approval_status == "PENDING":
        db.add(UserLoginLog(
            user_id=user.id, email=user.email, name=user.name,
            role=user.role, login_result="FAILED_PENDING", ip_address=ip
        ))
        db.commit()
        raise HTTPException(
            status_code=403,
            detail="您的帳號目前尚在『待審核』階段，請靜候系統管理者核准，或先點擊下方以『訪客』身份進入。"
        )

    if user.approval_status == "REJECTED":
        db.add(UserLoginLog(
            user_id=user.id, email=user.email, name=user.name,
            role=user.role, login_result="FAILED_REJECTED", ip_address=ip
        ))
        db.commit()
        raise HTTPException(status_code=403, detail="很抱歉，您的帳號權限申請未通過審核。")

    # 3. 檢查帳號啟用狀態
    if user.account_status != "ACTIVE":
        db.add(UserLoginLog(
            user_id=user.id, email=user.email, name=user.name,
            role=user.role, login_result="FAILED_DISABLED", ip_address=ip
        ))
        db.commit()
        raise HTTPException(status_code=403, detail="此帳號目前已被停用，請聯繫系統管理者。")

    # 4. 登入成功：累加登入次數 + 寫入 Log + 設定 Session
    user.login_count = (user.login_count or 0) + 1
    db.add(UserLoginLog(
        user_id=user.id,
        email=user.email,
        name=user.name,
        role=user.role,
        login_result="SUCCESS",
        ip_address=ip
    ))
    db.commit()

    session_data = {
        "id": user.id,
        "email": user.email,
        "name": user.name or user.email.split("@")[0],
        "role": user.role,
        "organization": user.organization
    }
    request.session["user"] = session_data

    return {
        "message": "登入成功",
        "user": session_data
    }


# =====================================================================
# API 3: 以『訪客』身份進入 (POST /api/auth/guest)
# =====================================================================
@router.post("/guest")
def enter_as_guest(request: Request, db: Session = Depends(get_db)):
    ip = get_client_ip(request)
    db.add(UserLoginLog(
        user_id=None,
        email="guest@visitor",
        name="訪客 (Guest)",
        role="訪客",
        login_result="GUEST",
        ip_address=ip
    ))
    db.commit()

    guest_session = {
        "id": None,
        "email": "guest@visitor",
        "name": "訪客",
        "role": "訪客",
        "organization": None
    }
    request.session["user"] = guest_session

    return {
        "message": "已切換為訪客身份",
        "user": guest_session
    }


# =====================================================================
# API 4: 註冊申請新帳號 (POST /api/auth/register)
# =====================================================================
class RegisterRequest(BaseModel):
    email: str
    password: str
    name: str                  # 必填：申請人真實姓名
    phone: str                 # 👈 改為必填：聯絡電話
    role: str = "會員"          # 預申請角色：'專家' | '會員'
    organization: str | None = None
    job_title: str | None = None

    @field_validator("email")
    @classmethod
    def validate_email(cls, v: str) -> str:
        clean_email = v.strip().lower()
        if not EMAIL_REGEX.match(clean_email):
            raise ValueError("帳號必須為有效的電子信箱格式（例如：name@domain.com）")
        return clean_email

    @field_validator("password")
    @classmethod
    def validate_password(cls, v: str) -> str:
        if len(v) < 6 or len(v) > 64:
            raise ValueError("密碼長度須介於 6 至 64 個字元之間")
        return v

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        cleaned = sanitize_user_field(v, max_len=30)
        if not cleaned:
            raise ValueError("請填寫申請人真實姓名（必填）")
        return cleaned

    @field_validator("phone")
    @classmethod
    def validate_phone(cls, v: str) -> str:
        cleaned = sanitize_user_field(v, max_len=25)
        if not cleaned:
            raise ValueError("請填寫聯絡電話（必填）")
        return cleaned


@router.post("/register")
def register_user(payload: RegisterRequest, db: Session = Depends(get_db)):
    # 檢查信箱是否已註冊
    existing = db.query(User).filter(User.email == payload.email).first()
    if existing:
        raise HTTPException(status_code=400, detail="此電子信箱已經註冊過，請直接登入或等待管理員審核！")

    # 限制預申請角色只能選「專家」或「會員」(防止惡意封包自封為系統管理者)
    allowed_apply_roles = ["專家", "會員"]
    applied_role = payload.role if payload.role in allowed_apply_roles else "會員"

    # 清洗選填欄位，防止 Indirect Prompt Injection
    new_user = User(
        email=payload.email,
        password_hash=hash_password(payload.password),
        name=payload.name,
        phone=payload.phone,
        role=applied_role,
        organization=sanitize_user_field(payload.organization, max_len=80),
        job_title=sanitize_user_field(payload.job_title, max_len=50),
        approval_status="PENDING",
        account_status="ACTIVE",
        login_count=0
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    return {
        "message": f"註冊申請已送出！申請人「{new_user.name}」預申請的角色為「{applied_role}」，待系統管理者審核通過後即可登入使用。",
        "email": new_user.email,
        "name": new_user.name,
        "role": new_user.role,
        "approval_status": new_user.approval_status
    }


# =====================================================================
# API 5: 登出 (POST /api/auth/logout)
# =====================================================================
@router.post("/logout")
def logout_user(request: Request):
    request.session.clear()
    return {"message": "已成功登出"}
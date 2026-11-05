# backend/app/models/user.py
from sqlalchemy import Column, Integer, String, Date, DateTime, ForeignKey, UniqueConstraint, func
from app.database import Base


class User(Base):
    """【第十一張表：users】使用者帳號與 RBAC 權限審核表"""
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(120), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)

    # 選填基本資料
    name = Column(String(50), nullable=True)
    organization = Column(String(100), nullable=True)
    job_title = Column(String(80), nullable=True)
    phone = Column(String(30), nullable=True)

    # RBAC 角色：'系統管理者' | '專家' | '會員'
    role = Column(String(30), nullable=False, default="會員", index=True)

    # 確認狀態 (審核)：'PENDING' (待審核) | 'APPROVED' (已通過) | 'REJECTED' (未通過)
    approval_status = Column(String(20), nullable=False, default="PENDING", index=True)

    # 帳號狀態：'ACTIVE' (啟用) | 'DISABLED' (停用)
    account_status = Column(String(20), nullable=False, default="ACTIVE")

    # 累計登入成功次數
    login_count = Column(Integer, nullable=False, default=0)

    # 核定時間 (已審核才會有時間)
    approved_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class UserLoginLog(Base):
    """【第十二張表：user_login_logs】使用者登入稽核紀錄表"""
    __tablename__ = "user_login_logs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    email = Column(String(120), nullable=False, index=True)
    name = Column(String(50), nullable=True)
    role = Column(String(30), nullable=False)

    # 登入結果：'SUCCESS' | 'GUEST' | 'FAILED_PWD' | 'FAILED_PENDING' | 'FAILED_REJECTED' | 'FAILED_DISABLED'
    login_result = Column(String(30), nullable=False)
    ip_address = Column(String(60), nullable=True)
    login_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)


class UserDailyQuota(Base):
    """【第十三張表：user_daily_quotas】使用者每日 Gemini API 提問次數與 Token 額度追蹤表"""
    __tablename__ = "user_daily_quotas"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    usage_date = Column(Date, nullable=False, index=True)  # 台灣時區日期 (YYYY-MM-DD)

    question_count = Column(Integer, nullable=False, default=0)
    prompt_tokens = Column(Integer, nullable=False, default=0)
    completion_tokens = Column(Integer, nullable=False, default=0)
    total_tokens = Column(Integer, nullable=False, default=0)

    last_asked_at = Column(DateTime(timezone=True), server_default=func.now())

    __table_args__ = (
        UniqueConstraint("user_id", "usage_date", name="uq_user_daily_quota"),
    )
# FastAPI 主程式入口，已設定好 CORS 跨域許可，讓 Vue 前端能無障礙呼叫 API。
# backend/app/main.py
import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.sessions import SessionMiddleware

from app.routers import search, review, meta, history, chat, auth, admin  # 👈 引入 search, review, meta, history, chat

app = FastAPI(title="KCC ToxProfiler API", version="1.0.0")

# 1. 掛載 SessionMiddleware (HttpOnly Cookie，保存 7 天)
SESSION_SECRET = os.getenv("SESSION_SECRET_KEY", "kcc-toxprofiler-super-secret-session-key-2026")
app.add_middleware(
    SessionMiddleware,
    secret_key=SESSION_SECRET,
    session_cookie="kcc_tox_session",
    max_age=60 * 60 * 24 * 7,
    same_site="lax",
    https_only=False
)

# 2. CORS 設定 (允許攜帶 Cookie credentials)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 3. 啟動時自動檢查並建立初始『系統管理者』帳號
@app.on_event("startup")
def on_startup():
    auth.ensure_initial_admin()

# 4. 註冊所有路由
app.include_router(search.router)
app.include_router(review.router) # 👈 註冊 review 路由
app.include_router(meta.router)  # 👈 註冊 meta 路由
app.include_router(history.router) # 👈 註冊 history
app.include_router(chat.router) # 👈 註冊 chat.router
app.include_router(auth.router) # 👈 註冊 auth.router
app.include_router(admin.router) # 👈 註冊 admin.router

@app.get("/")
def health_check():
    return {"status": "ok", "service": "KCC ToxProfiler FastAPI"}
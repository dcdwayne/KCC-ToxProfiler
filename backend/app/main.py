# FastAPI 主程式入口，已設定好 CORS 跨域許可，讓 Vue 前端能無障礙呼叫 API。
# backend/app/main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routers import search, review  # 👈 引入 review

app = FastAPI(title="KCC ToxProfiler API", version="1.0.0")

# 允許前端 Vue (localhost:5173 或 EC2:8080) 跨域請求
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 註冊首頁搜尋與篩選路由
app.include_router(search.router)
app.include_router(review.router) # 👈 註冊 review 路由

@app.get("/")
def health_check():
    return {"status": "ok", "service": "KCC ToxProfiler FastAPI"}
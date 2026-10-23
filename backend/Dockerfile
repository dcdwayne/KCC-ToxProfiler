# backend/Dockerfile
FROM python:3.11-slim

WORKDIR /app

# 安裝系統編譯與網路基礎工具
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc libpq-dev && \
    rm -rf /var/lib/apt/lists/*

# 先複製 requirements.txt 以利用 Docker 快取
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 複製 backend 所有程式碼與 scripts
COPY . .

# 設定 PYTHONPATH 讓 app 與 scripts 模組可互相引入
ENV PYTHONPATH=/app

EXPOSE 8000

# 啟動 FastAPI
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
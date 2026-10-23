# frontend/Dockerfile
"""
使用 Multi-stage build：第一階段用 Node 將 Vue 編譯成靜態檔 dist/，第二階段把 dist/ 放進極輕量的 Nginx 映像檔中（最終容器只佔 20 MB）：
"""
# --- 第一階段：使用 Node 編譯打包 Vue 3 專案 ---
FROM node:20-alpine AS build-stage

WORKDIR /app

COPY package*.json ./
RUN npm install

COPY . .
RUN npm run build

# --- 第二階段：使用 Nginx 掛載打包好的 dist 與反向代理設定 ---
FROM nginx:stable-alpine AS production-stage

# 複製自訂的 nginx.conf 覆蓋預設設定
COPY nginx.conf /etc/nginx/conf.d/default.conf

# 從第一階段複製打包好的靜態檔案至 Nginx 目錄
COPY --from=build-stage /app/dist /usr/share/nginx/html

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
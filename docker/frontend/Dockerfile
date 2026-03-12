# ============================================
# 多階段建置 - 前端 Vue 3 應用
# ============================================

# ============================================
# Stage 1: Build (建置階段)
# ============================================
FROM node:20-alpine as build

# 設定工作目錄
WORKDIR /app

# 複製 package.json 和 package-lock.json
COPY frontend/package*.json ./

# 安裝依賴
RUN npm ci

# 複製前端程式碼
COPY frontend/ ./

# 建置生產版本
RUN npm run build

# ============================================
# Stage 2: Production (生產階段 - Nginx)
# ============================================
FROM nginx:alpine as production

# 複製自訂 nginx 配置
COPY docker/nginx/nginx.conf /etc/nginx/nginx.conf

# 從 build stage 複製建置產物
COPY --from=build /app/dist /usr/share/nginx/html

# 暴露端口
EXPOSE 80

# 健康檢查
HEALTHCHECK --interval=30s --timeout=10s --start-period=10s --retries=3 \
    CMD wget --quiet --tries=1 --spider http://localhost/ || exit 1

# 啟動 Nginx
CMD ["nginx", "-g", "daemon off;"]

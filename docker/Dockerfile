# StockAI Multi-Stage Dockerfile

# Stage 1: Python Backend Builder
FROM python:3.11-slim as backend-builder

# 빌드 도구 설치
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    build-essential \
    libpq-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# 작업 디렉토리 설정
WORKDIR /app

# Python 의존성 설치
COPY requirements-minimal.txt ./
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements-minimal.txt

# NLTK 데이터 다운로드 (NLTK가 설치되어 있을 때만)
# RUN python -m nltk.downloader punkt stopwords wordnet averaged_perceptron_tagger

# Stage 2: Node.js Frontend Builder
FROM node:20-alpine as frontend-builder

WORKDIR /app/stockai-frontend

# 패키지 파일 복사 및 의존성 설치
COPY stockai-frontend/package*.json ./
RUN npm ci --only=production

# 프론트엔드 소스 복사 및 빌드
COPY stockai-frontend/ ./
RUN npm run build

# Stage 3: Final Runtime Image
FROM python:3.11-slim

# 런타임 의존성 설치
RUN apt-get update && apt-get install -y \
    libpq-dev \
    curl \
    supervisor \
    nginx \
    && rm -rf /var/lib/apt/lists/*

# 사용자 생성
RUN useradd -m -u 1000 stockai

WORKDIR /app

# Python 패키지 복사
COPY --from=backend-builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=backend-builder /usr/local/bin /usr/local/bin
COPY --from=backend-builder /root/nltk_data /home/stockai/nltk_data

# 애플리케이션 코드 복사
COPY --chown=stockai:stockai . .

# Next.js 빌드 결과물 복사
COPY --from=frontend-builder --chown=stockai:stockai /app/stockai-frontend/.next ./stockai-frontend/.next
COPY --from=frontend-builder --chown=stockai:stockai /app/stockai-frontend/public ./stockai-frontend/public
COPY --from=frontend-builder --chown=stockai:stockai /app/stockai-frontend/node_modules ./stockai-frontend/node_modules

# 로그 디렉토리 생성
RUN mkdir -p logs && chown -R stockai:stockai logs

# Nginx 설정
COPY docker/nginx.conf /etc/nginx/nginx.conf

# Supervisor 설정
COPY docker/supervisord.conf /etc/supervisor/conf.d/supervisord.conf

# 환경 변수 설정
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    NLTK_DATA=/home/stockai/nltk_data \
    NODE_ENV=production

# 포트 노출
EXPOSE 80 8200 3200

# 사용자 전환
USER stockai

# 헬스체크
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:8200/health || exit 1

# Supervisor로 모든 서비스 실행
CMD ["/usr/bin/supervisord", "-c", "/etc/supervisor/conf.d/supervisord.conf"]
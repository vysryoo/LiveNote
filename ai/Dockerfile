# =============================================================================
# LiveNote AI Gateway - Production Dockerfile
# =============================================================================

FROM python:3.11-slim

# 작업 디렉토리 설정
WORKDIR /app

# 시스템 패키지 업데이트 및 필수 도구 설치
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    gcc \
    g++ \
    git \
    && rm -rf /var/lib/apt/lists/*

# Python 의존성 먼저 복사 (캐시 활용)
COPY requirements.txt .

# Python 패키지 설치 (타임아웃 증가, 재시도 추가)
RUN pip install --no-cache-dir --upgrade pip setuptools wheel && \
    pip install --no-cache-dir --timeout=300 --retries=5 -r requirements.txt

# 프로젝트 전체 복사 (모듈 포함)
COPY . .

# 로컬 모듈을 editable mode로 설치
RUN pip install -e ./cap1_RAG_module && \
    pip install -e ./cap1_QA_module && \
    pip install -e ./cap1_openalex_module && \
    pip install -e ./cap1_wiki_module && \
    pip install -e ./cap1_youtube_module && \
    pip install -e ./cap1_google_module

# 데이터 저장 디렉토리 생성
RUN mkdir -p /app/server_storage/uploads \
             /app/server_storage/chroma_data \
             /app/server_storage/chroma_data_real

# 포트 노출
EXPOSE 8003

# 환경변수 설정
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

# 서버 실행
CMD ["uvicorn", "server.main:app", "--host", "0.0.0.0", "--port", "8003"]

# 🐳 LiveNote Docker 실행 가이드

LiveNote AI Gateway를 Docker로 쉽게 실행하는 방법입니다.

---

## 📋 사전 준비

### 1. Docker 설치 확인
```bash
docker --version
docker-compose --version
```

설치 안 되어 있으면:
- **Mac**: [Docker Desktop for Mac](https://docs.docker.com/desktop/install/mac-install/) 설치
- **Windows**: [Docker Desktop for Windows](https://docs.docker.com/desktop/install/windows-install/) 설치
- **Linux**: [Docker Engine](https://docs.docker.com/engine/install/) 설치

### 2. 환경 변수 설정
```bash
# .env 파일 생성 (예시에서 복사)
cp .env.example .env

# .env 파일 편집 (필수!)
vi .env  # 또는 nano .env
```

**필수 환경 변수:**
```env
OPENAI_API_KEY=sk-your-actual-key-here
YOUTUBE_API_KEY=your-youtube-api-key
NAVER_CLIENT_ID=your-naver-client-id
NAVER_CLIENT_SECRET=your-naver-client-secret
```

---

## 🚀 실행 방법

### 방법 1: Docker Compose 사용 (추천!) ⭐

**가장 간단한 방법입니다!**

```bash
# 1. 이미지 빌드 & 컨테이너 실행 (한 번에!)
docker-compose up --build

# 백그라운드 실행
docker-compose up -d --build

# 로그 확인
docker-compose logs -f

# 중지
docker-compose down

# 완전 삭제 (볼륨까지)
docker-compose down -v
```

### 방법 2: Docker 명령어 직접 사용

```bash
# 1. 이미지 빌드
docker build -t livenote-gateway .

# 2. 컨테이너 실행
docker run -d \
  --name livenote-gateway \
  -p 8003:8003 \
  --env-file .env \
  -v $(pwd)/server_storage:/app/server_storage \
  livenote-gateway

# 3. 로그 확인
docker logs -f livenote-gateway

# 4. 중지
docker stop livenote-gateway

# 5. 삭제
docker rm livenote-gateway
```

---

## ✅ 정상 작동 확인

### 1. Health Check
```bash
curl http://localhost:8003/health
# 출력: {"status":"ok"}
```

### 2. API 문서 확인
브라우저에서:
- Swagger UI: http://localhost:8003/docs
- ReDoc: http://localhost:8003/redoc

### 3. 간단한 테스트
```bash
# 텍스트 업서트 테스트
curl -X POST "http://localhost:8003/rag/text-upsert" \
  -H "Content-Type: application/json" \
  -d '{
    "lecture_id": "test_001",
    "items": [
      {
        "text": "Docker로 실행하는 LiveNote 서버입니다.",
        "metadata": {"source": "docker_test"}
      }
    ]
  }'
```

---

## 🔧 유용한 명령어

### 컨테이너 관리
```bash
# 실행 중인 컨테이너 확인
docker ps

# 모든 컨테이너 확인
docker ps -a

# 컨테이너 내부 접속
docker exec -it livenote-gateway bash

# 컨테이너 재시작
docker restart livenote-gateway
```

### 이미지 관리
```bash
# 이미지 목록
docker images

# 이미지 삭제
docker rmi livenote-gateway

# 미사용 이미지 정리
docker image prune -a
```

### 로그 & 디버깅
```bash
# 실시간 로그 보기
docker logs -f livenote-gateway

# 최근 100줄만
docker logs --tail 100 livenote-gateway

# 컨테이너 상태 확인
docker inspect livenote-gateway
```

---

## 📁 데이터 영속성

컨테이너를 삭제해도 데이터가 보존됩니다:
- `./server_storage/uploads/` - 업로드된 PDF
- `./server_storage/chroma_data/` - Vector DB 데이터

**전체 초기화하려면:**
```bash
docker-compose down -v
rm -rf server_storage/*
```

---

## 🐛 문제 해결

### 1. 포트 충돌 (8003번 포트 이미 사용 중)
```bash
# 다른 포트로 변경
docker run -p 9000:8003 ...  # 9000번 포트로 접근

# 또는 docker-compose.yml 수정
ports:
  - "9000:8003"
```

### 2. 환경 변수 안 들어감
```bash
# .env 파일 경로 확인
ls -la .env

# 수동으로 환경변수 전달
docker run -e OPENAI_API_KEY=sk-xxx ...
```

### 3. 빌드 실패
```bash
# 캐시 없이 재빌드
docker-compose build --no-cache

# 또는
docker build --no-cache -t livenote-gateway .
```

### 4. 컨테이너가 바로 종료됨
```bash
# 로그 확인
docker logs livenote-gateway

# 주로 환경변수 누락이나 모듈 import 오류
```

---

## 🎯 프로덕션 배포

### 환경 변수 분리
```bash
# 개발용
docker-compose --env-file .env.dev up

# 프로덕션용
docker-compose --env-file .env.prod up
```

### 리소스 제한
```yaml
# docker-compose.yml
services:
  livenote-api:
    deploy:
      resources:
        limits:
          cpus: '2'
          memory: 4G
        reservations:
          cpus: '1'
          memory: 2G
```

---

## 📞 도움말

- **API 문서**: http://localhost:8003/docs
- **상태 확인**: http://localhost:8003/health
- **이슈 리포트**: GitHub Issues

---

## 🎉 완료!

서버가 성공적으로 실행되었습니다! 🚀

```bash
# 서버 접속
curl http://localhost:8003/health

# API 탐색
open http://localhost:8003/docs
```

# 🚀 LiveNote API 배포 가이드

## AWS EC2 배포 (추천)

### 방법 A: Docker Hub 사용 (프로덕션 추천 ⭐)

**장점:** 빠른 배포 (30초), 안정적, 롤백 쉬움

```bash
# EC2에 접속 후
sudo yum update -y  # Amazon Linux
sudo yum install -y docker
sudo service docker start
sudo usermod -a -G docker ec2-user

# 재로그인 후
docker pull yourusername/livenote-api:latest

# .env 파일 준비
cat > .env << 'EOF'
OPENAI_API_KEY=your_key_here
RAG_PERSIST_DIR=server_storage/chroma_data
UPLOAD_DIR=server_storage/uploads
EOF

# 실행
docker run -d \
  --name livenote-api \
  -p 8003:8003 \
  --env-file .env \
  -v ./server_storage:/app/server_storage \
  --restart unless-stopped \
  yourusername/livenote-api:latest

# 보안 그룹에서 8003 포트 열기
# 확인: http://your-ec2-ip:8003/health
```

### 방법 B: GitHub Clone + Build (개발/테스트용)

**장점:** 코드 수정 즉시 반영

**주의:** t2.medium 이상 추천 (t2.micro는 메모리 부족 가능)

```bash
# EC2에 접속 후
sudo yum update -y
sudo yum install -y docker git
sudo service docker start
sudo usermod -a -G docker ec2-user

# 재로그인 후
git clone https://github.com/Team-GongGong-s/module_intergration.git
cd module_intergration

# .env 파일 준비
cp .env.example .env
nano .env  # API 키 입력

# 빌드 & 실행 (5-10분 소요)
docker-compose up -d --build

# 확인
curl http://localhost:8003/health
```

### 메모리 부족 시 스왑 설정
```bash
# t2.micro 사용 시 필수
sudo dd if=/dev/zero of=/swapfile bs=128M count=16
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile
echo '/swapfile swap swap defaults 0 0' | sudo tee -a /etc/fstab
```

## 빠른 시작 (로컬 테스트용)

### 1. Docker Hub에서 받기 (이미지 공유 후)
```bash
# 이미지 다운로드
docker pull yourusername/livenote-api:latest

# .env 파일 준비
cat > .env << 'EOF'
OPENAI_API_KEY=your_openai_key
RAG_PERSIST_DIR=server_storage/chroma_data
UPLOAD_DIR=server_storage/uploads
EOF

# 실행
docker run -d \
  --name livenote-api \
  -p 8003:8003 \
  --env-file .env \
  -v ./server_storage:/app/server_storage \
  --restart unless-stopped \
  yourusername/livenote-api:latest

# 확인
curl http://localhost:8003/health
```

### 2. tar 파일로 받은 경우
```bash
# 이미지 로드
docker load < livenote-api.tar

# .env 준비 (위와 동일)

# 실행
docker run -d \
  --name livenote-api \
  -p 8003:8003 \
  --env-file .env \
  -v ./server_storage:/app/server_storage \
  --restart unless-stopped \
  livenote-gateway
```

## 이미지 빌드 & 공유 (개발자용)

### Docker Hub에 업로드
```bash
# 1. 빌드
docker-compose build

# 2. 로그인
docker login

# 3. 태그
docker tag livenote-gateway yourusername/livenote-api:latest
docker tag livenote-gateway yourusername/livenote-api:v1.0.0

# 4. 푸시
docker push yourusername/livenote-api:latest
docker push yourusername/livenote-api:v1.0.0
```

### tar 파일로 저장
```bash
# 이미지 저장 (압축)
docker save livenote-gateway | gzip > livenote-api.tar.gz

# 로드
gunzip -c livenote-api.tar.gz | docker load
```

## 관리 명령어

```bash
# 로그 확인
docker logs -f livenote-api

# 중지
docker stop livenote-api

# 재시작
docker restart livenote-api

# 완전 삭제 (데이터 포함)
docker stop livenote-api
docker rm livenote-api
rm -rf ./server_storage
```

## 포트 변경

```bash
# 다른 포트로 실행 (예: 9000)
docker run -d \
  --name livenote-api \
  -p 9000:8003 \
  --env-file .env \
  -v ./server_storage:/app/server_storage \
  livenote-gateway
```

## 프로덕션 배포

### docker-compose 사용 (추천)
```yaml
# docker-compose.prod.yml
version: '3.8'
services:
  livenote-api:
    image: yourusername/livenote-api:latest
    container_name: livenote-gateway
    ports:
      - "8003:8003"
    volumes:
      - ./server_storage:/app/server_storage
    env_file:
      - .env
    restart: always
    deploy:
      resources:
        limits:
          cpus: '2'
          memory: 4G
```

```bash
# 실행
docker-compose -f docker-compose.prod.yml up -d
```

## 필요한 파일

1. **Docker 이미지** (Docker Hub 또는 tar)
2. **`.env`** - API 키 설정
3. **`server_storage/`** - 데이터 저장 디렉토리 (자동 생성됨)

## 문제 해결

### 포트 충돌
```bash
# 8003 포트 사용 중인 프로세스 확인
lsof -i :8003
# 또는
netstat -an | grep 8003

# 다른 포트 사용
docker run -p 9000:8003 ...
```

### 데이터 백업
```bash
# 백업
tar -czf server_storage_backup.tar.gz server_storage/

# 복원
tar -xzf server_storage_backup.tar.gz
```

## API 문서

서버 실행 후:
- Swagger UI: http://localhost:8003/docs
- ReDoc: http://localhost:8003/redoc

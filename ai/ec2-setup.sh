#!/bin/bash
# EC2 초기 설정 스크립트

set -e

echo "🚀 LiveNote API EC2 초기 설정 시작..."

# Docker 설치
echo "[1/5] Docker 설치 중..."
sudo yum update -y
sudo yum install -y docker
sudo service docker start
sudo usermod -a -G docker ec2-user

# Docker Compose 설치
echo "[2/5] Docker Compose 설치 중..."
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# 스왑 메모리 설정 (t2.micro용)
echo "[3/5] 스왑 메모리 설정 중..."
if [ ! -f /swapfile ]; then
  sudo dd if=/dev/zero of=/swapfile bs=128M count=16
  sudo chmod 600 /swapfile
  sudo mkswap /swapfile
  sudo swapon /swapfile
  echo '/swapfile swap swap defaults 0 0' | sudo tee -a /etc/fstab
  echo "✅ 스왑 메모리 2GB 생성 완료"
else
  echo "⏭️  스왑 파일이 이미 존재합니다"
fi

# 디렉토리 생성
echo "[4/5] 디렉토리 생성 중..."
mkdir -p ~/livenote/server_storage/{uploads,chroma_data}

# .env 템플릿 생성
echo "[5/5] .env 템플릿 생성 중..."
cat > ~/livenote/.env << 'EOF'
# OpenAI API Key (필수)
OPENAI_API_KEY=your_openai_api_key_here

# RAG 설정
RAG_PERSIST_DIR=server_storage/chroma_data
UPLOAD_DIR=server_storage/uploads

# 선택사항
# RAG_CHUNK_SIZE=1000
# RAG_CHUNK_OVERLAP=200
# RAG_MAX_TOKENS=500
EOF

echo ""
echo "✅ 설정 완료!"
echo ""
echo "📝 다음 단계:"
echo "1. 재로그인: exit 후 다시 접속 (Docker 그룹 적용)"
echo "2. .env 수정: nano ~/livenote/.env"
echo "3. 이미지 실행:"
echo "   cd ~/livenote"
echo "   docker pull yourusername/livenote-api:latest"
echo "   docker run -d --name livenote-api -p 8003:8003 --env-file .env -v ./server_storage:/app/server_storage --restart unless-stopped yourusername/livenote-api:latest"
echo ""
echo "또는 GitHub에서 빌드:"
echo "   git clone https://github.com/Team-GongGong-s/module_intergration.git ~/livenote"
echo "   cd ~/livenote"
echo "   nano .env"
echo "   docker-compose up -d --build"

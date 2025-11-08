#!/bin/bash

echo "=================================="
echo "🚀 STT 서버 설치 스크립트"
echo "=================================="

# 1. Python 버전 확인
echo ""
echo "📍 Python 버전 확인 중..."
if ! command -v python3 &> /dev/null; then
    echo "❌ Python3가 설치되어 있지 않습니다."
    echo "   Python 3.8 이상을 설치해주세요: https://www.python.org/"
    exit 1
fi

PYTHON_VERSION=$(python3 --version 2>&1 | grep -oP '\d+\.\d+')
echo "✅ Python $PYTHON_VERSION 감지됨"

# 2. 가상환경 생성
echo ""
echo "📦 가상환경 생성 중..."
if [ -d ".venv" ]; then
    echo "⚠️  기존 .venv 폴더가 있습니다. 삭제하고 다시 생성할까요? (y/n)"
    read -r response
    if [[ "$response" =~ ^[Yy]$ ]]; then
        rm -rf .venv
        echo "🗑️  기존 .venv 폴더 삭제됨"
    else
        echo "⏭️  기존 .venv 사용"
    fi
fi

if [ ! -d ".venv" ]; then
    python3 -m venv .venv
    echo "✅ 가상환경 생성 완료"
else
    echo "✅ 가상환경 이미 존재함"
fi

# 3. 가상환경 활성화
echo ""
echo "🔄 가상환경 활성화 중..."
source .venv/bin/activate
echo "✅ 가상환경 활성화됨"

# 4. pip 업그레이드
echo ""
echo "📦 pip 업그레이드 중..."
python -m pip install --upgrade pip --quiet
echo "✅ pip 업그레이드 완료"

# 5. 패키지 설치
echo ""
echo "📥 패키지 설치 중..."
pip install -r requirements.txt --quiet
echo "✅ 패키지 설치 완료"

# 6. .env 파일 생성
echo ""
if [ ! -f ".env" ]; then
    echo "📄 .env 파일 생성 중..."
    cp .env.example .env
    echo "✅ .env 파일 생성됨"
    echo ""
    echo "⚠️  중요: .env 파일을 열어서 OPENAI_API_KEY를 설정해주세요!"
    echo "   파일 위치: $(pwd)/.env"
else
    echo "✅ .env 파일 이미 존재함"
fi

# 7. 설치 완료
echo ""
echo "=================================="
echo "✅ 설치 완료!"
echo "=================================="
echo ""
echo "📋 다음 단계:"
echo "   1. .env 파일에 OPENAI_API_KEY 설정"
echo "   2. 서버 실행: python app.py"
echo "   3. 테스트 페이지 접속: http://localhost:8003/test"
echo ""
echo "🔧 유용한 명령어:"
echo "   - 가상환경 활성화: source .venv/bin/activate"
echo "   - 가상환경 비활성화: deactivate"
echo "   - 서버 실행: python app.py"
echo ""

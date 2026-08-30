#!/bin/bash

# OpenAlexKit 모듈 환경 설정 스크립트

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🔧 OpenAlexKit 환경 설정"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# 1. 가상환경 생성
if [ ! -d ".venv" ]; then
    echo "📦 가상환경 생성 중..."
    python3 -m venv .venv
    echo "✅ 가상환경 생성 완료"
else
    echo "✅ 가상환경이 이미 존재합니다"
fi

# 2. 가상환경 활성화
echo "🔌 가상환경 활성화 중..."
source .venv/bin/activate

# 3. pip 업그레이드
echo "⬆️  pip 업그레이드 중..."
pip install --upgrade pip -q

# 4. 의존성 설치
echo "📚 패키지 설치 중..."
pip install -e . -q

# 5. .env 파일 확인
if [ ! -f ".env" ]; then
    echo "⚠️  .env 파일이 없습니다. 생성합니다..."
    echo "OPENAI_API_KEY=your-api-key-here" > .env
    echo "❌ .env 파일을 열어서 OPENAI_API_KEY를 설정해주세요!"
    echo "   파일 위치: $(pwd)/.env"
else
    # API 키 확인
    if grep -q "your-api-key-here" .env || ! grep -q "OPENAI_API_KEY=sk-" .env; then
        echo "⚠️  .env 파일의 OPENAI_API_KEY를 확인해주세요!"
    else
        echo "✅ .env 파일 설정 완료"
    fi
fi

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "✨ 환경 설정 완료!"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "📌 다음 단계:"
echo "1. .env 파일에 OpenAI API 키 설정 (필요시)"
echo "2. 가상환경 실행: source .venv/bin/activate"
echo "3. 테스트 실행: python test_openalex.py"
echo ""

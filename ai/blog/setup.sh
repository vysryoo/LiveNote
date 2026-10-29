#!/bin/bash

echo "🚀 GoogleKit 설치 시작..."

# 가상환경 활성화 확인
if [[ -z "$VIRTUAL_ENV" ]]; then
    echo "⚠️  경고: 가상환경이 활성화되지 않았습니다."
    echo "   가상환경을 먼저 활성화해주세요: source .venv/bin/activate"
    exit 1
fi

# 의존성 설치
echo "📦 의존성 설치 중..."
pip install -e .

if [ $? -eq 0 ]; then
    echo "✅ GoogleKit 설치 완료!"
else
    echo "❌ 설치 실패"
    exit 1
fi

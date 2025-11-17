#!/usr/bin/env bash
# LiveNote Docker 간편 실행 스크립트

set -e

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "${PROJECT_ROOT}"

echo "🐳 LiveNote Docker 실행 도구"
echo "================================"

# .env 파일 확인
if [ ! -f ".env" ]; then
    echo "⚠️  .env 파일이 없습니다!"
    if [ -f ".env.example" ]; then
        echo "📄 .env.example을 .env로 복사합니다..."
        cp .env.example .env
        echo "✅ .env 파일 생성 완료"
        echo ""
        echo "⚠️  중요: .env 파일을 편집하여 실제 API 키를 입력하세요!"
        echo "   vi .env"
        echo ""
        read -p "계속하시겠습니까? (y/n) " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            exit 1
        fi
    else
        echo "❌ .env.example 파일도 없습니다!"
        exit 1
    fi
fi

# Docker 설치 확인
if ! command -v docker &> /dev/null; then
    echo "❌ Docker가 설치되어 있지 않습니다!"
    echo "   https://docs.docker.com/get-docker/"
    exit 1
fi

if ! command -v docker-compose &> /dev/null; then
    echo "❌ Docker Compose가 설치되어 있지 않습니다!"
    echo "   https://docs.docker.com/compose/install/"
    exit 1
fi

echo ""
echo "선택하세요:"
echo "1) 빌드 & 실행 (포그라운드)"
echo "2) 빌드 & 실행 (백그라운드)"
echo "3) 중지"
echo "4) 로그 보기"
echo "5) 완전 삭제 (데이터 포함)"
echo ""
read -p "선택 (1-5): " choice

case $choice in
    1)
        echo "🚀 서버를 빌드하고 실행합니다 (Ctrl+C로 종료)..."
        docker-compose up --build
        ;;
    2)
        echo "🚀 서버를 백그라운드로 실행합니다..."
        docker-compose up -d --build
        echo ""
        echo "✅ 서버 실행 완료!"
        echo "   • 상태 확인: curl http://localhost:8003/health"
        echo "   • API 문서: http://localhost:8003/docs"
        echo "   • 로그 보기: docker-compose logs -f"
        echo "   • 중지: docker-compose down"
        ;;
    3)
        echo "⏸️  서버를 중지합니다..."
        docker-compose down
        echo "✅ 중지 완료"
        ;;
    4)
        echo "📋 로그를 표시합니다 (Ctrl+C로 종료)..."
        docker-compose logs -f
        ;;
    5)
        echo "⚠️  경고: 모든 컨테이너와 데이터가 삭제됩니다!"
        read -p "정말 삭제하시겠습니까? (yes 입력): " confirm
        if [ "$confirm" = "yes" ]; then
            echo "🗑️  삭제 중..."
            docker-compose down -v
            docker rmi livenote-gateway 2>/dev/null || true
            echo "✅ 삭제 완료"
        else
            echo "취소되었습니다."
        fi
        ;;
    *)
        echo "❌ 잘못된 선택입니다."
        exit 1
        ;;
esac

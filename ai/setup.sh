#!/usr/bin/env bash
# AI 서버 실행 환경 구축: uv로 Python 3.11 가상환경(.venv)과 의존성(uv.lock)을 맞추고 .env를 준비함

set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "${PROJECT_ROOT}"

if ! command -v uv >/dev/null 2>&1; then
  echo "uv가 없습니다. 설치 후 다시 실행하세요: brew install uv 또는 https://docs.astral.sh/uv/"
  exit 1
fi

# Python 3.11이 없으면 uv가 내려받음
uv sync

if [ ! -f .env ] && [ -f .env.example ]; then
  echo ".env 파일이 없어 .env.example을 복사함. 키 값을 채워야 함"
  cp .env.example .env
fi

cat <<'MSG'
설치 완료

1) 환경 변수 확인:  vi .env
2) 서버 실행:       uv run uvicorn server.main:app --reload --port 8003
3) 테스트:          uv run pytest
MSG

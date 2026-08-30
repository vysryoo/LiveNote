#!/usr/bin/env bash
# FastAPI 서버 실행 환경 부트스트랩 스크립트

set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV_DIR="${PROJECT_ROOT}/.venv"
REQUIREMENTS_FILE="${PROJECT_ROOT}/requirements.server.txt"
ENV_EXAMPLE="${PROJECT_ROOT}/.env.example"

PYTHON_BIN_DEFAULT="python3"
PYTHON_BIN="${PYTHON_BIN:-$PYTHON_BIN_DEFAULT}"
if ! command -v "${PYTHON_BIN}" >/dev/null 2>&1; then
  echo "⚠️  ${PYTHON_BIN} 을(를) 찾을 수 없습니다. 기본값(${PYTHON_BIN_DEFAULT})으로 시도합니다."
  PYTHON_BIN="${PYTHON_BIN_DEFAULT}"
fi
if ! command -v "${PYTHON_BIN}" >/dev/null 2>&1; then
  echo "❌ ${PYTHON_BIN_DEFAULT} 실행 파일을 찾을 수 없습니다. PYTHON_BIN 환경변수로 버전을 지정하세요."
  exit 1
fi

echo "🔧 프로젝트 루트: ${PROJECT_ROOT}"
echo "🔧 가상환경 경로: ${VENV_DIR}"
echo "🔧 Python: ${PYTHON_BIN}"

# Git Submodule 초기화 확인
if [ -f "${PROJECT_ROOT}/.gitmodules" ]; then
  echo "📦 Git Submodule 확인 중..."
  
  # 서브모듈이 초기화되었는지 확인
  SUBMODULE_EMPTY=false
  while IFS= read -r line; do
    if [[ "$line" =~ path[[:space:]]*=[[:space:]]*(.+) ]]; then
      SUBMODULE_PATH="${BASH_REMATCH[1]}"
      SUBMODULE_PATH="${SUBMODULE_PATH// /}"  # 공백 제거
      
      # 서브모듈 디렉토리가 비어있는지 확인
      if [ -d "${PROJECT_ROOT}/${SUBMODULE_PATH}" ] && [ -z "$(ls -A "${PROJECT_ROOT}/${SUBMODULE_PATH}" 2>/dev/null)" ]; then
        SUBMODULE_EMPTY=true
        break
      fi
    fi
  done < "${PROJECT_ROOT}/.gitmodules"
  
  # 서브모듈이 비어있으면 초기화
  if [ "$SUBMODULE_EMPTY" = true ]; then
    echo "📦 Git Submodule 초기화 중..."
    git -C "${PROJECT_ROOT}" submodule update --init --recursive
    echo "✅ Git Submodule 초기화 완료"
  else
    echo "✅ Git Submodule 이미 초기화됨"
  fi
fi

NEED_CREATE=true
if [ -d "${VENV_DIR}" ] && [ -x "${VENV_DIR}/bin/python" ]; then
  VENV_PY_VERSION="$("${VENV_DIR}/bin/python" -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')"
  if [ "${VENV_PY_VERSION}" = "3.11" ]; then
    NEED_CREATE=false
  else
    echo "⚠️  기존 가상환경은 Python ${VENV_PY_VERSION} 버전입니다. 재생성합니다."
    rm -rf "${VENV_DIR}"
  fi
fi

if [ "${NEED_CREATE}" = true ]; then
  echo "📦 가상환경 생성 중 (Python 3.11)..."
  "${PYTHON_BIN}" -m venv "${VENV_DIR}"
fi

echo "📦 가상환경 활성화..."
# shellcheck source=/dev/null
source "${VENV_DIR}/bin/activate"

echo "📦 pip 업그레이드..."
pip install --upgrade pip setuptools wheel

if [ ! -f "${REQUIREMENTS_FILE}" ]; then
  echo "❌ ${REQUIREMENTS_FILE} 파일을 찾을 수 없습니다."
  exit 1
fi

echo "📦 서버 통합 의존성 설치..."
pip install -r "${REQUIREMENTS_FILE}"

echo "📦 로컬 모듈 설치 (editable mode)..."
pip install -e "${PROJECT_ROOT}/cap1_RAG_module"
pip install -e "${PROJECT_ROOT}/cap1_QA_module"
pip install -e "${PROJECT_ROOT}/cap1_openalex_module"
pip install -e "${PROJECT_ROOT}/cap1_wiki_module"
pip install -e "${PROJECT_ROOT}/cap1_youtube_module"
pip install -e "${PROJECT_ROOT}/cap1_google_module"

if [ ! -f "${PROJECT_ROOT}/.env" ]; then
  if [ -f "${ENV_EXAMPLE}" ]; then
    echo "📄 .env 파일이 없어 .env.example을 복사합니다."
    cp "${ENV_EXAMPLE}" "${PROJECT_ROOT}/.env"
  fi
fi

ACTIVATE_SCRIPT="${VENV_DIR}/bin/activate"
ENV_MARKER="# >>> project .env >>>"
if [ -f "${PROJECT_ROOT}/.env" ] && [ -f "${ACTIVATE_SCRIPT}" ] && ! grep -q "${ENV_MARKER}" "${ACTIVATE_SCRIPT}"; then
  cat <<'EOF' >> "${ACTIVATE_SCRIPT}"
# >>> project .env >>>
if [ -f "$VIRTUAL_ENV/../.env" ]; then
  _OLD_IFS="$IFS"
  set -a
  . "$VIRTUAL_ENV/../.env"
  set +a
  IFS="$_OLD_IFS"
fi
# <<< project .env <<<
EOF
fi

cat <<'EOF'
✅ 설치 완료!

1) 환경 변수 확인/수정:   vi .env
2) 가상환경 활성화:       source .venv/bin/activate
3) 서버 실행:           uvicorn server.main:app --reload --port 8003

필요 시 PYTHON_BIN=python3.11 ./setup.sh 처럼 Python 버전을 지정할 수 있습니다.
EOF

#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV_DIR="${ROOT_DIR}/.venv"

if [ -f "${VENV_DIR}/bin/activate" ]; then
  # shellcheck disable=SC1090
  source "${VENV_DIR}/bin/activate"
else
  echo "[!] .venv/bin/activate 를 찾을 수 없습니다. ./setup.sh 를 먼저 실행하세요." >&2
  exit 1
fi

HOST=${HOST:-127.0.0.1}
PORT=${PORT:-8000}
UVICORN_BIN="${VENV_DIR}/bin/uvicorn"
APP="server.main:app"
LOG_FILE="${ROOT_DIR}/tmp_uvicorn.log"

started_server=false

if ! pgrep -f "${APP}" >/dev/null 2>&1; then
  echo "[*] FastAPI 서버를 시작합니다..."
  "${UVICORN_BIN}" "${APP}" --host "${HOST}" --port "${PORT}" >/tmp/tmp_uvicorn.log 2>&1 &
  SERVER_PID=$!
  started_server=true
  sleep 3
else
  echo "[*] 기존에 실행 중인 FastAPI 서버를 사용합니다."
fi

cleanup() {
  if [ "${started_server}" = true ] && kill -0 "${SERVER_PID}" >/dev/null 2>&1; then
    echo
    echo "[*] FastAPI 서버를 중지합니다 (PID: ${SERVER_PID})..."
    kill "${SERVER_PID}" >/dev/null 2>&1 || true
  fi
}
trap cleanup EXIT

echo "[*] Health 체크를 수행합니다..."
curl -s "http://$HOST:$PORT/health" || { echo "[!] Health 체크 실패" >&2; exit 1; }
echo

LECTURE_ID="mp101"

echo "[*] 멀티프로세싱 30초 분량 텍스트 3개를 업서트합니다..."
curl -sS -X POST "http://$HOST:$PORT/rag/text-upsert" \
     -H "Content-Type: application/json" \
     -d @- <<JSON
{
  "lecture_id": "${LECTURE_ID}",
  "items": [
    {
      "text": "멀티프로세싱은 여러 개의 프로세스를 동시에 실행하여 CPU 코어를 완전히 활용하는 병렬 처리 방식입니다. 30초짜리 데모에서는 각 프로세스가 독립된 메모리 공간을 사용하며 상호 간섭 없이 태스크를 분담하는 모습을 보여줍니다.",
      "metadata": {"duration":"30s","topic":"멀티프로세싱 기초"}
    },
    {
      "text": "두 번째 데모에서는 이미지 변환 작업을 네 개의 프로세스로 나누어 처리합니다. 각 프로세스가 별도의 큐에서 업무를 가져가고, 완료된 결과를 메인 프로세스가 수집해 합치는 과정까지 30초 안에 시연됩니다.",
      "metadata": {"duration":"30s","topic":"병렬 이미지 처리"}
    },
    {
      "text": "세 번째 예시에서는 과학 계산을 여러 프로세스로 분할하여 실행합니다. 프로세스 간 통신은 파이프를 통해 이뤄지고, 계산 완료 후 결과를 병합하는 흐름을 30초 동안 순차적으로 설명합니다.",
      "metadata": {"duration":"30s","topic":"과학 계산 분할"}
    }
  ]
}
JSON
echo

SECTION_SUMMARY="하이퍼 스레딩은 하나의 물리 코어가 두 개의 명령 흐름을 번갈아 실행하여 자원을 더 효율적으로 쓰도록 설계된 동시 멀티스레딩 기술이다."

echo "[*] QA 스트림을 요청합니다 (하이퍼 스레딩)..."
curl --no-buffer --max-time 30 -sS -N -X POST "http://$HOST:$PORT/qa/generate" \
     -H "Content-Type: application/json" \
     -d @- <<JSON
{
  "lecture_id": "${LECTURE_ID}",
  "section_id": 1,
  "section_summary": "${SECTION_SUMMARY}"
}
JSON
echo

echo "[*] REC 스트림을 요청합니다 (하이퍼 스레딩)..."
curl --no-buffer --max-time 30 -sS -N -X POST "http://$HOST:$PORT/rec/recommend" \
     -H "Content-Type: application/json" \
     -d @- <<JSON
{
  "lecture_id": "${LECTURE_ID}",
  "section_id": 1,
  "section_summary": "${SECTION_SUMMARY}",
  "previous_summaries": [],
  "yt_exclude": [],
  "wiki_exclude": [],
  "paper_exclude": []
}
JSON
echo

echo "[*] 테스트 완료"

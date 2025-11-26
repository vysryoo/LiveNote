#!/usr/bin/env bash
set -uo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
HOST=${HOST:-127.0.0.1}
PORT=${PORT:-8003}
BASE_URL="http://${HOST}:${PORT}"

CALLBACK_QA=${CALLBACK_QA:-https://webhook.site/65c1525f-da82-4d45-a8c8-351a004429d7}
CALLBACK_REC=${CALLBACK_REC:-https://webhook.site/65c1525f-da82-4d45-a8c8-351a004429d7}
LECTURE_ID=${LECTURE_ID:-7777}
SUMMARY_ID=${SUMMARY_ID:-101}

SECTION_SUMMARY="하이퍼 스레딩은 하나의 물리 코어가 두 개의 명령 흐름을 번갈아 실행하여 자원을 효율적으로 쓰도록 설계된 동시 멀티스레딩 기술이다."
ALT_SECTION_SUMMARY="인터럽트와 컨텍스트 스위칭 동작을 비교하며 커널 스케줄러가 태스크를 분배하는 방식을 설명한다."

print_case() {
  local title="$1"
  printf "\n%s\n# %s\n%s\n" "==================================================" "${title}" "=================================================="
}

call_api() {
  local title="$1"
  local payload="$2"
  local url="$3"
  local method="${4:-POST}"
  print_case "${title}"
  if [ "${method}" = "GET" ]; then
    echo "--- Request ---"
    echo "(GET) ${url}"
  else
    echo "--- Request JSON ---"
    echo "${payload}"
  fi
  local tmp
  tmp="$(mktemp)"
  local status
  if [ "${method}" = "GET" ]; then
    if ! status=$(curl -sS -o "${tmp}" -w '%{http_code}' "${url}"); then
      echo "[!] curl 요청 실패 (${title})" >&2
      rm -f "${tmp}"
      return
    fi
  else
    if ! status=$(curl -sS -o "${tmp}" -w '%{http_code}' "${url}" -H "Content-Type: application/json" -d "${payload}"); then
      echo "[!] curl 요청 실패 (${title})" >&2
      rm -f "${tmp}"
      return
    fi
  fi
  echo "--- Response (${status}) ---"
  if [ -s "${tmp}" ]; then
    if ! python -m json.tool <"${tmp}" 2>/dev/null; then
      cat "${tmp}"
    fi
  else
    echo "(빈 응답 바디)"
  fi
  rm -f "${tmp}"
}

echo "Target host : ${BASE_URL}"
echo "QA callback : ${CALLBACK_QA}"
echo "REC callback: ${CALLBACK_REC}"
echo "Lecture ID  : ${LECTURE_ID}"

usage() {
  cat <<EOF
사용법: ./test_multi.sh [케이스번호 ...]
미입력 시 1~6 전체 실행.
케이스:
  1. Health check
  2. RAG text upsert
  3. QA 기본 question_types
  4. QA 커스텀 question_types
  5. REC 모든 provider
  6. REC WIKI+VIDEO만
  7. QA 이전 질문 제공 (개념 타입 중복 방지)
  8. REC 논문 제외 목록 추가
EOF
}

USER_INPUT=""
if [ "$#" -eq 0 ]; then
  echo
  read -r -p "몇 번을 실행하시겠습니까? (예: 1 3 5, 엔터=전체) > " USER_INPUT || true
  if [ -z "${USER_INPUT}" ]; then
    SELECTED=("1" "2" "3" "4" "5" "6")
  else
    # 공백 구분 숫자 배열
    SELECTED=(${USER_INPUT})
  fi
else
  SELECTED=("$@")
fi

# 요청 본문 정의
PAYLOAD_HEALTH="{}"
PAYLOAD_RAG=$(cat <<JSON
{
  "lecture_id": "${LECTURE_ID}",
  "items": [
    {"text": "멀티프로세싱은 여러 개의 프로세스를 동시에 실행하여 CPU 자원을 효율적으로 활용하는 병렬 처리 방식이다.", "metadata": {"topic": "멀티프로세싱", "duration": "30s"}},
    {"text": "이미지 변환 작업을 네 개의 프로세스로 나누어 처리하면 전체 처리 시간을 단축할 수 있다.", "metadata": {"topic": "이미지 처리", "duration": "30s"}},
    {"text": "과학 계산을 여러 프로세스로 분할하여 실행하고 결과를 병합하는 흐름을 설명한다.", "metadata": {"topic": "과학 계산", "duration": "30s"}}
  ]
}
JSON
)
PAYLOAD_QA_DEFAULT=$(cat <<JSON
{
  "lecture_id": ${LECTURE_ID},
  "summary_id": ${SUMMARY_ID},
  "section_index": 0,
  "section_summary": "${SECTION_SUMMARY}",
  "subject": "운영체제",
  "callback_url": "${CALLBACK_QA}",
  "previous_qa": [
    {
      "type": "개념",
      "question": "멀티프로세싱과 멀티스레딩의 차이점은 무엇인가요?",
      "answer": "멀티프로세싱은 프로세스 간 독립된 메모리를 사용하고 멀티스레딩은 메모리를 공유합니다."
    }
  ]
}
JSON
)
PAYLOAD_QA_CUSTOM=$(cat <<JSON
{
  "lecture_id": ${LECTURE_ID},
  "summary_id": ${SUMMARY_ID}01,
  "section_index": 1,
  "section_summary": "${ALT_SECTION_SUMMARY}",
  "subject": "운영체제",
  "callback_url": "${CALLBACK_QA}",
  "question_types": ["CONCEPT", "ADVANCED", "COMPARISON"],
  "previous_qa": []
}
JSON
)
PAYLOAD_REC_ALL=$(cat <<JSON
{
  "lecture_id": ${LECTURE_ID},
  "summary_id": ${SUMMARY_ID},
  "section_index": 0,
  "section_summary": "${SECTION_SUMMARY}",
  "callback_url": "${CALLBACK_REC}",
  "previous_summaries": [],
  "yt_exclude": ["기존 유튜브 제목"],
  "wiki_exclude": ["기존 위키 제목"],
  "paper_exclude": ["old-paper-id"],
  "google_exclude": ["http://old.example.com"]
}
JSON
)
PAYLOAD_REC_FILTERED=$(cat <<JSON
{
  "lecture_id": ${LECTURE_ID},
  "summary_id": ${SUMMARY_ID}02,
  "section_index": 2,
  "section_summary": "${ALT_SECTION_SUMMARY}",
  "callback_url": "${CALLBACK_REC}",
  "previous_summaries": [],
  "yt_exclude": ["이전 유튜브"],
  "wiki_exclude": ["이전 위키"],
  "paper_exclude": ["무시될 paper"],
  "google_exclude": ["무시될 google"],
  "resource_types": ["WIKI", "VIDEO"]
}
JSON
)
PAYLOAD_QA_PREVIOUS=$(cat <<JSON
{
  "lecture_id": ${LECTURE_ID},
  "summary_id": ${SUMMARY_ID}03,
  "section_index": 0,
  "section_summary": "${SECTION_SUMMARY}",
  "subject": "운영체제",
  "callback_url": "${CALLBACK_QA}",
  "question_types": ["CONCEPT"],
  "previous_qa": [
    {
      "type": "CONCEPT",
      "question": "하이퍼 스레딩이 CPU 자원 효율성에 미치는 영향은 무엇인가요?",
      "answer": "하이퍼 스레딩은 하나의 물리적 코어가 두 개의 명령 흐름을 번갈아 실행하도록 하여 CPU 자원을 효율적으로 사용하게 합니다. 이를 통해 CPU의 유휴 시간을 줄이고, 동시에 더 많은 작업을 처리할 수 있습니다. 결과적으로, 시스템의 전반적인 성능이 향상될 수 있으며, 특히 멀티스레드 애플리케이션에서 그 효과가 두드러집니다."
    }
  ]
}
JSON
)
PAYLOAD_REC_EXCLUDE_PAPER=$(cat <<JSON
{
  "lecture_id": ${LECTURE_ID},
  "summary_id": ${SUMMARY_ID}04,
  "section_index": 3,
  "section_summary": "${SECTION_SUMMARY}",
  "callback_url": "${CALLBACK_REC}",
  "previous_summaries": [],
  "yt_exclude": [],
  "wiki_exclude": [],
  "paper_exclude": [
    "https://doi.org/10.1109/pact.2003.1237999",
    "https://openalex.org/W87616783"
  ],
  "google_exclude": []
}
JSON
)

for CASE in "${SELECTED[@]}"; do
  case "${CASE}" in
    1) call_api "01) Health check" "${PAYLOAD_HEALTH}" "${BASE_URL}/health" "GET" ;;
    2) call_api "02) RAG text upsert (3 items)" "${PAYLOAD_RAG}" "${BASE_URL}/rag/text-upsert" ;;
    3) call_api "03) QA generate (default types)" "${PAYLOAD_QA_DEFAULT}" "${BASE_URL}/qa/generate" ;;
    4) call_api "04) QA generate (question_types override)" "${PAYLOAD_QA_CUSTOM}" "${BASE_URL}/qa/generate" ;;
    5) call_api "05) REC recommend (all providers)" "${PAYLOAD_REC_ALL}" "${BASE_URL}/rec/recommend" ;;
    6) call_api "06) REC recommend (WIKI + VIDEO only)" "${PAYLOAD_REC_FILTERED}" "${BASE_URL}/rec/recommend" ;;
    7) call_api "07) QA generate (with previous CONCEPT to avoid duplicates)" "${PAYLOAD_QA_PREVIOUS}" "${BASE_URL}/qa/generate" ;;
    8) call_api "08) REC recommend (paper excludes applied)" "${PAYLOAD_REC_EXCLUDE_PAPER}" "${BASE_URL}/rec/recommend" ;;
    *) echo "[!] 알 수 없는 케이스 번호: ${CASE}" ;;
  esac
done

echo
echo "[완료] 실행한 케이스: ${SELECTED[*]}"
echo "콜백 응답 확인:"
echo "  - 기본 설정은 httpbin 콜백으로 요청을 echo합니다 (CALLBACK_QA/REC)."
echo "  - webhook.site 등을 CALLBACK_QA/CALLBACK_REC로 지정하면 브라우저에서 콜백 payload를 바로 볼 수 있습니다."

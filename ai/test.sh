#!/usr/bin/env bash
set -euo pipefail

HOST=${HOST:-127.0.0.1}
PORT=${PORT:-8000}

echo "[*] Checking health..."
curl -s "http://$HOST:$PORT/health" || { echo "Health check failed" >&2; exit 1; }
echo

echo "[*] Upserting sample text..."
curl -s -X POST "http://$HOST:$PORT/rag/text-upsert" \
     -H "Content-Type: application/json" \
     -d "{\"lecture_id\":\"test-lecture\",\"items\":[{\"text\":\"샘플 요약입니다\"}]}"
echo

echo "[*] Triggering REC SSE (single chunk)..."
curl -s -N -X POST "http://$HOST:$PORT/rec/recommend" \
     -H "Content-Type: application/json" \
     -d "{\"lecture_id\":\"test-lecture\",\"section_id\":1,\"section_summary\":\"샘플 섹션\",\"previous_summaries\":[],\"yt_exclude\":[],\"wiki_exclude\":[],\"paper_exclude\":[]}"
echo
echo "Done"

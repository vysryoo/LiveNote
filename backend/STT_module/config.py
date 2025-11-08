"""
STT 서버 설정
환경변수 기반 설정 관리
"""
import os
from dotenv import load_dotenv

# 환경변수 로드
load_dotenv()

# ===========================
# 🔑 OpenAI API 설정
# ===========================
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    raise ValueError("❌ OPENAI_API_KEY가 설정되지 않았습니다. .env 파일을 확인하세요.")

# ===========================
# 🌐 서버 설정
# ===========================
HOST = os.getenv("STT_HOST", "localhost")
PORT = int(os.getenv("STT_PORT", 8003))

# ===========================
# 🔌 WebSocket 엔드포인트 설정
# ===========================
WEBSOCKET_ENDPOINT = os.getenv("WEBSOCKET_ENDPOINT", "/ws/stt")

# ===========================
# 🤖 OpenAI Realtime API 설정
# ===========================
REALTIME_MODEL = os.getenv("REALTIME_MODEL", "gpt-4o-realtime-preview-2024-10-01")
TRANSCRIPTION_MODEL = os.getenv("TRANSCRIPTION_MODEL", "gpt-4o-transcribe")
LANGUAGE = os.getenv("LANGUAGE", "ko")

# ===========================
# 🎤 오디오 설정
# ===========================
SAMPLE_RATE = int(os.getenv("SAMPLE_RATE", 24000))  # 24kHz (Realtime API 필수)
CHANNELS = int(os.getenv("CHANNELS", 1))  # Mono
CHUNK_DURATION_MS = int(os.getenv("CHUNK_DURATION_MS", 200))  # 0.2초

# ===========================
# 🎯 VAD (Voice Activity Detection) 설정
# ===========================
VAD_ENABLED = os.getenv("VAD_ENABLED", "true").lower() == "true"
VAD_THRESHOLD = float(os.getenv("VAD_THRESHOLD", 0.5))  # 음성 감지 임계값 (0~1)
VAD_PREFIX_PADDING_MS = int(os.getenv("VAD_PREFIX_PADDING_MS", 300))  # 음성 시작 전 패딩
VAD_SILENCE_DURATION_MS = int(os.getenv("VAD_SILENCE_DURATION_MS", 500))  # 무음 지속 시간

# ===========================
# 🔗 API URL
# ===========================
REALTIME_API_URL = f"wss://api.openai.com/v1/realtime?model={REALTIME_MODEL}"

# ===========================
# 📊 로깅 설정
# ===========================
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")

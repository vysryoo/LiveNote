# 📁 STT 모듈 구조

```
STT_module/
│
├── 📄 app.py                    # FastAPI 서버 메인 파일
├── 📄 config.py                 # 환경 설정 관리
├── 📄 stt_session.py            # OpenAI Realtime API 세션 관리
│
├── 📦 requirements.txt          # Python 패키지 의존성
├── 🔧 setup.sh                  # 자동 설치 스크립트
├── 🔐 .env.example              # 환경변수 예제
├── 🚫 .gitignore               # Git 제외 파일 목록
│
├── 📖 README.md                 # 전체 문서
├── 🚀 QUICKSTART.md            # 빠른 시작 가이드
├── 🎨 FRONTEND_GUIDE.md        # 프론트엔드 통합 가이드
│
├── 🌐 example_client.html      # 예제 HTML 클라이언트
└── 📜 stt_client.js            # 예제 JavaScript 클라이언트
```

---

## 🔑 핵심 파일 설명

### `app.py`
- FastAPI 서버 메인 애플리케이션
- WebSocket 엔드포인트 (`/ws/stt`)
- 테스트 페이지 제공 (`/test`)
- 루트 엔드포인트 (서버 상태 확인)

**주요 기능:**
- WebSocket 연결 관리
- 오디오 청크 수신 및 OpenAI로 전달
- 전사 결과 클라이언트로 전송
- 오류 처리 및 로깅

---

### `config.py`
- 환경변수 기반 설정 관리
- `.env` 파일 로드
- 모든 설정값 중앙 관리

**주요 설정:**
- `OPENAI_API_KEY`: OpenAI API 키
- `STT_HOST`, `STT_PORT`: 서버 주소/포트
- `LANGUAGE`: 전사 언어 (기본: 한국어)
- `VAD_ENABLED`: 음성 감지 활성화 여부
- `SAMPLE_RATE`: 오디오 샘플레이트 (24kHz)

---

### `stt_session.py`
- OpenAI Realtime API 세션 관리
- WebSocket 이벤트 처리
- 성능 측정 및 로깅

**주요 클래스:**
- `RealtimeSTTSession`: 세션 관리 클래스
  - `connect_to_openai()`: OpenAI 연결
  - `configure_session()`: 세션 설정 (언어, VAD 등)
  - `send_audio()`: 오디오 전송
  - `listen_openai_events()`: 이벤트 수신
  - `handle_openai_event()`: 이벤트 처리

---

### `requirements.txt`
- Python 패키지 의존성 목록

```
fastapi==0.115.6          # FastAPI 웹 프레임워크
uvicorn[standard]==0.34.0 # ASGI 서버
websockets==14.1          # WebSocket 라이브러리
python-dotenv==1.0.1      # 환경변수 로드
```

---

### `setup.sh`
- 자동 설치 스크립트
- 가상환경 생성 및 패키지 설치
- `.env` 파일 생성

**실행:**
```bash
chmod +x setup.sh
./setup.sh
```

---

### `.env.example`
- 환경변수 예제 파일
- 실제 사용 시 `.env`로 복사 후 수정

**필수 설정:**
```bash
OPENAI_API_KEY=your_api_key_here
```

---

### 문서 파일들

#### `README.md`
- 전체 프로젝트 문서
- 설치, 설정, API 문서, 트러블슈팅

#### `QUICKSTART.md`
- 5분 빠른 시작 가이드
- 초보자용 단계별 안내

#### `FRONTEND_GUIDE.md`
- 프론트엔드 통합 상세 가이드
- JavaScript, React, Vue.js 예제
- WebSocket 프로토콜 상세 설명

---

### 예제 파일들

#### `example_client.html`
- 브라우저 기반 테스트 클라이언트
- 마이크 입력 → WebSocket → 전사 결과 표시
- UI/UX 예제

#### `stt_client.js`
- JavaScript 클라이언트 구현
- WebSocket 연결 및 이벤트 처리
- 오디오 캡처 및 PCM16 변환
- Base64 인코딩 및 전송

---

## 🔄 데이터 흐름

```
1. 클라이언트 (브라우저)
   ↓ [마이크 입력]
   
2. JavaScript
   ↓ [Float32 → Int16 → Base64]
   
3. WebSocket
   ↓ [{"type": "audio", "audio": "base64..."}]
   
4. app.py (FastAPI)
   ↓ [WebSocket 수신]
   
5. stt_session.py
   ↓ [OpenAI Realtime API로 전달]
   
6. OpenAI Realtime API
   ↓ [음성 → 텍스트 변환]
   
7. stt_session.py
   ↓ [이벤트 처리]
   
8. app.py
   ↓ [WebSocket 전송]
   
9. JavaScript
   ↓ [{"type": "transcript_completed", "text": "안녕하세요"}]
   
10. 클라이언트 (브라우저)
    ↓ [UI 업데이트]
```

---

## 🎯 주요 이벤트 타입

### 클라이언트 → 서버
- `audio`: 오디오 청크 전송
- `stop`: 녹음 중지

### 서버 → 클라이언트
- `transcript_delta`: 실시간 전사 (부분 결과)
- `transcript_completed`: 전사 완료 (최종 결과)
- `speech_started`: 음성 감지 시작 (VAD)
- `speech_stopped`: 음성 감지 종료 (VAD)
- `error`: 오류 발생
- `info`: 정보 메시지

---

## 🔧 환경 변수

| 변수 | 기본값 | 설명 |
|------|--------|------|
| `OPENAI_API_KEY` | (필수) | OpenAI API 키 |
| `STT_HOST` | `localhost` | 서버 호스트 |
| `STT_PORT` | `8003` | 서버 포트 |
| `REALTIME_MODEL` | `gpt-4o-realtime-preview-2024-10-01` | Realtime API 모델 |
| `TRANSCRIPTION_MODEL` | `gpt-4o-transcribe` | 전사 모델 |
| `LANGUAGE` | `ko` | 전사 언어 |
| `SAMPLE_RATE` | `24000` | 샘플레이트 (Hz) |
| `CHANNELS` | `1` | 채널 수 |
| `CHUNK_DURATION_MS` | `200` | 청크 길이 (ms) |
| `VAD_ENABLED` | `true` | VAD 활성화 |
| `VAD_THRESHOLD` | `0.5` | VAD 임계값 |
| `VAD_PREFIX_PADDING_MS` | `300` | VAD 시작 패딩 |
| `VAD_SILENCE_DURATION_MS` | `500` | VAD 무음 지속 시간 |
| `LOG_LEVEL` | `INFO` | 로그 레벨 |

---

## 📊 성능 측정

`stt_session.py`는 다음 성능 지표를 자동으로 측정합니다:

- ⚡ **첫 응답 지연시간**: 첫 오디오 → 첫 전사 델타
- ⏱️ **전사 완료 시간**: 발화 종료 → 전사 완료
- 📊 **평균 전사 간격**: 전사 이벤트 간 평균 시간
- 📍 **총 발화 시간**: 전체 음성 세그먼트 길이

**로그 예시:**
```
⚡ 첫 응답 지연시간: 0.52초 (첫 오디오 → 첫 델타)
⏱️  발화 종료 → 전사 완료: 0.31초
📊 평균 전사 간격: 2.15초 (전사 5개)
```

---

## 🚀 배포 체크리스트

- [ ] Python 3.8 이상 설치
- [ ] `./setup.sh` 실행
- [ ] `.env` 파일에 `OPENAI_API_KEY` 설정
- [ ] `python app.py`로 서버 실행
- [ ] `http://localhost:8003/test`에서 테스트
- [ ] 프론트엔드에서 `ws://localhost:8003/ws/stt` 연결
- [ ] 마이크 권한 허용
- [ ] 전사 결과 확인

---

## 📞 문의

문제가 발생하거나 궁금한 점이 있으면 팀에 문의하세요!

---

**Made with ❤️ for Frontend Team**

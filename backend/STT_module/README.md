# 🎤 STT FastAPI 서버

프론트엔드 팀 테스트용 실시간 음성 인식 서버

**OpenAI Realtime API** 기반 WebSocket STT 서버

---

## 📋 목차

1. [빠른 시작](#-빠른-시작)
2. [기능](#-기능)
3. [설치 방법](#-설치-방법)
4. [환경 설정](#-환경-설정)
5. [서버 실행](#-서버-실행)
6. [API 문서](#-api-문서)
7. [프론트엔드 통합 가이드](#-프론트엔드-통합-가이드)
8. [트러블슈팅](#-트러블슈팅)

---

## 🚀 빠른 시작

```bash
# 1. 설치 스크립트 실행
chmod +x setup.sh
./setup.sh

# 2. .env 파일에 OpenAI API 키 설정
# .env 파일을 열어서 OPENAI_API_KEY를 입력하세요

# 3. 서버 실행
python app.py

# 4. 브라우저에서 테스트
# http://localhost:8003/test
```

---

## ✨ 기능

- ✅ **실시간 음성 인식** (OpenAI Realtime API)
- ✅ **WebSocket 기반** 양방향 통신
- ✅ **VAD (Voice Activity Detection)** 지원
- ✅ **한국어 최적화** (기본 언어: 한국어)
- ✅ **실시간 전사 델타** (부분 결과)
- ✅ **완료된 전사 결과** (최종 결과)
- ✅ **성능 측정** (지연시간, 전사 간격 등)
- ✅ **테스트 페이지** 내장

---

## 📦 설치 방법

### 요구사항

- Python 3.8 이상
- OpenAI API 키 (Realtime API 접근 권한 필요)

### 자동 설치 (권장)

```bash
chmod +x setup.sh
./setup.sh
```

### 수동 설치

```bash
# 1. 가상환경 생성
python3 -m venv .venv

# 2. 가상환경 활성화 (macOS/Linux)
source .venv/bin/activate

# 3. 패키지 설치
pip install -r requirements.txt

# 4. .env 파일 생성
cp .env.example .env
```

---

## ⚙️ 환경 설정

`.env` 파일을 생성하고 다음 값들을 설정하세요:

```bash
# 🔑 필수 설정
OPENAI_API_KEY=your_openai_api_key_here

# 🌐 서버 설정 (선택)
STT_HOST=localhost
STT_PORT=8003

# 🔌 WebSocket 엔드포인트 설정 (선택)
WEBSOCKET_ENDPOINT=/ws/stt

# 🤖 Realtime API 설정 (선택)
REALTIME_MODEL=gpt-4o-realtime-preview-2024-10-01
TRANSCRIPTION_MODEL=gpt-4o-transcribe
LANGUAGE=ko

# 🎤 오디오 설정 (선택)
SAMPLE_RATE=24000        # 24kHz (Realtime API 필수)
CHANNELS=1               # Mono
CHUNK_DURATION_MS=200    # 0.2초

# 🎯 VAD 설정 (선택)
VAD_ENABLED=true
VAD_THRESHOLD=0.5
VAD_PREFIX_PADDING_MS=300
VAD_SILENCE_DURATION_MS=500

# 📊 로깅 설정 (선택)
LOG_LEVEL=INFO
```

---

## 🏃 서버 실행

### 기본 실행

```bash
python app.py
```

### 커스텀 포트로 실행

```bash
# .env 파일에서 STT_PORT 수정하거나
STT_PORT=9000 python app.py
```

### 실행 확인

서버가 정상적으로 실행되면 다음과 같은 로그가 출력됩니다:

```
============================================================
🚀 STT 서버 시작
📍 주소: http://localhost:8003
🔌 WebSocket: ws://localhost:8003/ws/stt
🧪 테스트 페이지: http://localhost:8003/test
🎯 VAD 활성화: True
============================================================
```

---

## 📚 API 문서

### 1. 루트 엔드포인트

**GET** `/`

서버 상태 및 엔드포인트 정보 확인

**응답:**
```json
{
  "status": "running",
  "message": "✅ STT 서버가 정상 작동 중입니다.",
  "endpoints": {
    "websocket": "ws://localhost:8003/ws/stt",
    "test_page": "http://localhost:8003/test"
  }
}
```

### 2. 테스트 페이지

**GET** `/test`

브라우저에서 직접 테스트할 수 있는 HTML 페이지

### 3. WebSocket 엔드포인트

**WebSocket** `/ws/stt`

실시간 음성 인식 WebSocket 연결

#### 클라이언트 → 서버 메시지

**오디오 전송:**
```json
{
  "type": "audio",
  "audio": "<base64-encoded-pcm16>"
}
```

**녹음 중지:**
```json
{
  "type": "stop"
}
```

#### 서버 → 클라이언트 메시지

**실시간 전사 (델타):**
```json
{
  "type": "transcript_delta",
  "text": "안녕하",
  "item_id": "item_abc123",
  "timestamp": "2024-01-01T12:00:00.000Z"
}
```

**전사 완료:**
```json
{
  "type": "transcript_completed",
  "text": "안녕하세요",
  "item_id": "item_abc123",
  "timestamp": "2024-01-01T12:00:01.000Z"
}
```

**음성 감지 시작:**
```json
{
  "type": "speech_started",
  "timestamp": "2024-01-01T12:00:00.000Z"
}
```

**음성 감지 종료:**
```json
{
  "type": "speech_stopped",
  "timestamp": "2024-01-01T12:00:05.000Z"
}
```

**오류:**
```json
{
  "type": "error",
  "message": "오류 메시지"
}
```

**정보:**
```json
{
  "type": "info",
  "message": "정보 메시지"
}
```

---

## 🎨 프론트엔드 통합 가이드

### 1. 오디오 형식 요구사항

- **포맷**: PCM16 (16-bit Linear PCM)
- **샘플레이트**: 24000 Hz (24kHz)
- **채널**: 1 (Mono)
- **인코딩**: Base64

### 2. JavaScript 예제 코드

#### 기본 연결

```javascript
// WebSocket 연결
const ws = new WebSocket('ws://localhost:8003/ws/stt');

ws.onopen = () => {
  console.log('✅ WebSocket 연결됨');
};

ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  
  switch(data.type) {
    case 'transcript_delta':
      console.log('📝 [실시간]', data.text);
      // UI 업데이트: 실시간 텍스트 표시
      break;
      
    case 'transcript_completed':
      console.log('✅ [완료]', data.text);
      // UI 업데이트: 최종 텍스트 저장
      break;
      
    case 'speech_started':
      console.log('🎤 음성 감지 시작');
      // UI 업데이트: 녹음 중 표시
      break;
      
    case 'speech_stopped':
      console.log('⏸️ 음성 감지 종료');
      // UI 업데이트: 대기 표시
      break;
      
    case 'error':
      console.error('❌ 오류:', data.message);
      // 오류 처리
      break;
  }
};

ws.onerror = (error) => {
  console.error('WebSocket 오류:', error);
};

ws.onclose = () => {
  console.log('🔌 WebSocket 연결 종료');
};
```

#### 오디오 캡처 및 전송

```javascript
// 마이크 권한 요청
const stream = await navigator.mediaDevices.getUserMedia({
  audio: {
    channelCount: 1,
    sampleRate: 24000,
    echoCancellation: true,
    noiseSuppression: true
  }
});

// AudioContext 생성
const audioContext = new AudioContext({ sampleRate: 24000 });
const source = audioContext.createMediaStreamSource(stream);
const processor = audioContext.createScriptProcessor(4096, 1, 1);

processor.onaudioprocess = (e) => {
  const inputData = e.inputBuffer.getChannelData(0);
  const pcm16 = new Int16Array(inputData.length);
  
  // Float32 → Int16 변환
  for (let i = 0; i < inputData.length; i++) {
    const s = Math.max(-1, Math.min(1, inputData[i]));
    pcm16[i] = s < 0 ? s * 0x8000 : s * 0x7FFF;
  }
  
  // Base64 인코딩
  const base64 = btoa(String.fromCharCode.apply(null, new Uint8Array(pcm16.buffer)));
  
  // WebSocket으로 전송
  if (ws.readyState === WebSocket.OPEN) {
    ws.send(JSON.stringify({
      type: 'audio',
      audio: base64
    }));
  }
};

source.connect(processor);
processor.connect(audioContext.destination);
```

#### 녹음 중지

```javascript
// 녹음 중지 신호 전송
ws.send(JSON.stringify({ type: 'stop' }));

// AudioContext 정리
audioContext.close();

// WebSocket 연결 종료
ws.close();
```

### 3. React 예제

```jsx
import { useEffect, useRef, useState } from 'react';

function STTComponent() {
  const [transcript, setTranscript] = useState('');
  const [isRecording, setIsRecording] = useState(false);
  const wsRef = useRef(null);
  const audioContextRef = useRef(null);

  const startRecording = async () => {
    // WebSocket 연결
    wsRef.current = new WebSocket('ws://localhost:8003/ws/stt');
    
    wsRef.current.onmessage = (event) => {
      const data = JSON.parse(event.data);
      
      if (data.type === 'transcript_completed') {
        setTranscript(prev => prev + data.text + '\n');
      }
    };
    
    // 오디오 캡처 (위의 JavaScript 예제 참고)
    // ...
    
    setIsRecording(true);
  };

  const stopRecording = () => {
    wsRef.current?.send(JSON.stringify({ type: 'stop' }));
    wsRef.current?.close();
    audioContextRef.current?.close();
    setIsRecording(false);
  };

  return (
    <div>
      <button onClick={startRecording} disabled={isRecording}>
        녹음 시작
      </button>
      <button onClick={stopRecording} disabled={!isRecording}>
        녹음 중지
      </button>
      <pre>{transcript}</pre>
    </div>
  );
}
```

---

## 🐛 트러블슈팅

### 1. "OPENAI_API_KEY가 설정되지 않았습니다" 오류

**원인**: `.env` 파일에 OpenAI API 키가 없음

**해결**:
```bash
# .env 파일을 열어서 다음을 추가
OPENAI_API_KEY=sk-your-api-key-here
```

### 2. "OpenAI Realtime API 연결 실패" 오류

**원인**: API 키가 잘못되었거나 Realtime API 접근 권한이 없음

**해결**:
- OpenAI API 키가 유효한지 확인
- Realtime API 접근 권한 확인 (베타 기능)

### 3. "마이크 권한 오류"

**원인**: 브라우저에서 마이크 권한이 거부됨

**해결**:
- 브라우저 설정에서 마이크 권한 허용
- HTTPS 환경에서 테스트 (localhost는 예외)

### 4. "연결이 자주 끊김"

**원인**: 네트워크 불안정 또는 오디오 청크 전송 문제

**해결**:
- 네트워크 연결 확인
- VAD 설정 조정 (`.env` 파일)
- `CHUNK_DURATION_MS` 값 조정

### 5. "전사 결과가 영어로 나옴"

**원인**: 언어 설정이 잘못됨

**해결**:
```bash
# .env 파일에서 언어 설정 확인
LANGUAGE=ko
```

### 6. "포트가 이미 사용 중" 오류

**원인**: 8003 포트가 이미 사용 중

**해결**:
```bash
# .env 파일에서 다른 포트로 변경
STT_PORT=9000
```

---

## 📞 문의

문제가 발생하거나 궁금한 점이 있으면 팀에 문의하세요!

---

## 📄 라이선스

내부 프로젝트용

---

**Made with ❤️ for Frontend Team**

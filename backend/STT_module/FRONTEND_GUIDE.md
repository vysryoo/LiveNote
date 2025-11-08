# 🎨 프론트엔드 통합 가이드

STT 서버를 프론트엔드 애플리케이션에 통합하는 상세 가이드

---

## 📋 목차

1. [WebSocket 프로토콜](#-websocket-프로토콜)
2. [오디오 형식 요구사항](#-오디오-형식-요구사항)
3. [JavaScript 통합 예제](#-javascript-통합-예제)
4. [React 통합 예제](#-react-통합-예제)
5. [Vue.js 통합 예제](#-vuejs-통합-예제)
6. [오류 처리](#-오류-처리)
7. [성능 최적화](#-성능-최적화)
8. [FAQ](#-faq)

---

## 🔌 WebSocket 프로토콜

### 연결 엔드포인트

```
ws://localhost:8003/ws/stt  (.env에서 엔드포인트 (path) 수정 가능)
```

### 메시지 형식

#### 클라이언트 → 서버

**1. 오디오 전송**
```json
{
  "type": "audio",
  "audio": "<base64-encoded-pcm16>"
}
```

**2. 녹음 중지**
```json
{
  "type": "stop"
}
```

#### 서버 → 클라이언트

**1. 실시간 전사 (델타)**
```json
{
  "type": "transcript_delta",
  "text": "안녕하",
  "item_id": "item_abc123",
  "timestamp": "2024-01-01T12:00:00.000Z"
}
```

**2. 전사 완료**
```json
{
  "type": "transcript_completed",
  "text": "안녕하세요",
  "item_id": "item_abc123",
  "timestamp": "2024-01-01T12:00:01.000Z"
}
```

**3. 음성 감지 시작 (VAD 활성화 시)**
```json
{
  "type": "speech_started",
  "timestamp": "2024-01-01T12:00:00.000Z"
}
```

**4. 음성 감지 종료 (VAD 활성화 시)**
```json
{
  "type": "speech_stopped",
  "timestamp": "2024-01-01T12:00:05.000Z"
}
```

**5. 오류**
```json
{
  "type": "error",
  "message": "오류 메시지"
}
```

**6. 정보**
```json
{
  "type": "info",
  "message": "정보 메시지"
}
```

---

## 🎤 오디오 형식 요구사항

### 필수 사양

- **포맷**: PCM16 (16-bit Linear PCM)
- **샘플레이트**: 24000 Hz (24kHz) - **반드시 지켜야 함**
- **채널**: 1 (Mono)
- **인코딩**: Base64
- **엔디안**: Little-endian

### 권장 설정

```javascript
const audioConfig = {
  sampleRate: 24000,          // 24kHz (필수!)
  channelCount: 1,            // Mono
  echoCancellation: true,     // 에코 제거
  noiseSuppression: true,     // 노이즈 제거
  autoGainControl: true       // 자동 게인 조절
};
```

### 오디오 처리 파이프라인

```
마이크 입력 
  → MediaStream 
  → AudioContext (24kHz)
  → ScriptProcessor
  → Float32 → Int16 변환
  → Base64 인코딩
  → WebSocket 전송
```

---

## 💻 JavaScript 통합 예제

### 1. 기본 설정

```javascript
// WebSocket 연결
const ws = new WebSocket('ws://localhost:8003/ws/stt');

// 오디오 설정
const audioConfig = {
  sampleRate: 24000,
  channelCount: 1,
  echoCancellation: true,
  noiseSuppression: true
};
```

### 2. WebSocket 이벤트 처리

```javascript
ws.onopen = () => {
  console.log('✅ WebSocket 연결됨');
  startAudioCapture();
};

ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  
  switch (data.type) {
    case 'transcript_delta':
      // 실시간 전사 업데이트
      updateTranscriptDelta(data.text);
      break;
      
    case 'transcript_completed':
      // 완료된 전사 저장
      saveTranscript(data.text);
      break;
      
    case 'speech_started':
      // UI: 음성 감지 중 표시
      showRecordingIndicator();
      break;
      
    case 'speech_stopped':
      // UI: 대기 상태 표시
      hideRecordingIndicator();
      break;
      
    case 'error':
      // 오류 처리
      handleError(data.message);
      break;
  }
};

ws.onerror = (error) => {
  console.error('❌ WebSocket 오류:', error);
};

ws.onclose = () => {
  console.log('🔌 WebSocket 연결 종료');
  cleanup();
};
```

### 3. 오디오 캡처 및 전송

```javascript
let audioContext;
let processor;
let mediaStream;

async function startAudioCapture() {
  try {
    // 마이크 권한 요청
    mediaStream = await navigator.mediaDevices.getUserMedia({
      audio: audioConfig
    });
    
    // AudioContext 생성 (24kHz!)
    audioContext = new AudioContext({ sampleRate: 24000 });
    
    // MediaStream → AudioContext
    const source = audioContext.createMediaStreamSource(mediaStream);
    
    // ScriptProcessor 생성
    processor = audioContext.createScriptProcessor(4096, 1, 1);
    
    // 오디오 데이터 처리
    processor.onaudioprocess = (e) => {
      const inputData = e.inputBuffer.getChannelData(0);
      const pcm16 = convertToPCM16(inputData);
      const base64 = arrayBufferToBase64(pcm16.buffer);
      
      // WebSocket으로 전송
      if (ws.readyState === WebSocket.OPEN) {
        ws.send(JSON.stringify({
          type: 'audio',
          audio: base64
        }));
      }
    };
    
    // AudioContext 연결
    source.connect(processor);
    processor.connect(audioContext.destination);
    
    console.log('🎙️ 오디오 캡처 시작');
    
  } catch (error) {
    console.error('❌ 오디오 캡처 오류:', error);
    throw error;
  }
}

// Float32 → Int16 변환
function convertToPCM16(float32Array) {
  const int16Array = new Int16Array(float32Array.length);
  
  for (let i = 0; i < float32Array.length; i++) {
    // -1.0 ~ 1.0 → -32768 ~ 32767
    const s = Math.max(-1, Math.min(1, float32Array[i]));
    int16Array[i] = s < 0 ? s * 0x8000 : s * 0x7FFF;
  }
  
  return int16Array;
}

// ArrayBuffer → Base64 변환
function arrayBufferToBase64(buffer) {
  const bytes = new Uint8Array(buffer);
  let binary = '';
  for (let i = 0; i < bytes.length; i++) {
    binary += String.fromCharCode(bytes[i]);
  }
  return btoa(binary);
}
```

### 4. 녹음 중지 및 정리

```javascript
function stopRecording() {
  // 서버에 중지 신호 전송
  if (ws && ws.readyState === WebSocket.OPEN) {
    ws.send(JSON.stringify({ type: 'stop' }));
  }
  
  cleanup();
}

function cleanup() {
  // AudioContext 정리
  if (processor) {
    processor.disconnect();
    processor = null;
  }
  
  if (audioContext) {
    audioContext.close();
    audioContext = null;
  }
  
  // MediaStream 정리
  if (mediaStream) {
    mediaStream.getTracks().forEach(track => track.stop());
    mediaStream = null;
  }
  
  // WebSocket 정리
  if (ws) {
    ws.close();
    ws = null;
  }
}
```

---

## ⚛️ React 통합 예제

### 1. useSTT 커스텀 훅

```jsx
import { useState, useRef, useCallback } from 'react';

function useSTT(wsUrl = 'ws://localhost:8003/ws/stt') {
  const [transcript, setTranscript] = useState('');
  const [isRecording, setIsRecording] = useState(false);
  const [isConnected, setIsConnected] = useState(false);
  const [error, setError] = useState(null);
  
  const wsRef = useRef(null);
  const audioContextRef = useRef(null);
  const processorRef = useRef(null);
  const mediaStreamRef = useRef(null);
  
  // 녹음 시작
  const startRecording = useCallback(async () => {
    try {
      setError(null);
      
      // WebSocket 연결
      wsRef.current = new WebSocket(wsUrl);
      
      wsRef.current.onopen = async () => {
        setIsConnected(true);
        
        // 마이크 권한 요청
        const stream = await navigator.mediaDevices.getUserMedia({
          audio: {
            sampleRate: 24000,
            channelCount: 1,
            echoCancellation: true,
            noiseSuppression: true
          }
        });
        
        mediaStreamRef.current = stream;
        
        // AudioContext 생성
        audioContextRef.current = new AudioContext({ sampleRate: 24000 });
        const source = audioContextRef.current.createMediaStreamSource(stream);
        processorRef.current = audioContextRef.current.createScriptProcessor(4096, 1, 1);
        
        // 오디오 처리
        processorRef.current.onaudioprocess = (e) => {
          const inputData = e.inputBuffer.getChannelData(0);
          const pcm16 = new Int16Array(inputData.length);
          
          for (let i = 0; i < inputData.length; i++) {
            const s = Math.max(-1, Math.min(1, inputData[i]));
            pcm16[i] = s < 0 ? s * 0x8000 : s * 0x7FFF;
          }
          
          const base64 = btoa(String.fromCharCode.apply(null, new Uint8Array(pcm16.buffer)));
          
          if (wsRef.current?.readyState === WebSocket.OPEN) {
            wsRef.current.send(JSON.stringify({ type: 'audio', audio: base64 }));
          }
        };
        
        source.connect(processorRef.current);
        processorRef.current.connect(audioContextRef.current.destination);
        
        setIsRecording(true);
      };
      
      wsRef.current.onmessage = (event) => {
        const data = JSON.parse(event.data);
        
        if (data.type === 'transcript_completed') {
          setTranscript(prev => prev + data.text + '\n');
        } else if (data.type === 'error') {
          setError(data.message);
        }
      };
      
      wsRef.current.onerror = (err) => {
        setError('WebSocket 연결 오류');
        console.error(err);
      };
      
      wsRef.current.onclose = () => {
        setIsConnected(false);
        setIsRecording(false);
      };
      
    } catch (err) {
      setError(err.message);
      console.error(err);
    }
  }, [wsUrl]);
  
  // 녹음 중지
  const stopRecording = useCallback(() => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify({ type: 'stop' }));
    }
    
    // 리소스 정리
    processorRef.current?.disconnect();
    audioContextRef.current?.close();
    mediaStreamRef.current?.getTracks().forEach(track => track.stop());
    wsRef.current?.close();
    
    setIsRecording(false);
  }, []);
  
  // 전사 내용 초기화
  const clearTranscript = useCallback(() => {
    setTranscript('');
  }, []);
  
  return {
    transcript,
    isRecording,
    isConnected,
    error,
    startRecording,
    stopRecording,
    clearTranscript
  };
}

export default useSTT;
```

### 2. STT 컴포넌트

```jsx
import React from 'react';
import useSTT from './useSTT';

function STTComponent() {
  const {
    transcript,
    isRecording,
    isConnected,
    error,
    startRecording,
    stopRecording,
    clearTranscript
  } = useSTT();
  
  return (
    <div style={{ padding: '20px' }}>
      <h1>🎤 실시간 음성 인식</h1>
      
      {/* 상태 표시 */}
      <div style={{ marginBottom: '20px' }}>
        상태: {isRecording ? '🔴 녹음 중' : isConnected ? '🟢 연결됨' : '⚪ 연결 안됨'}
      </div>
      
      {/* 오류 표시 */}
      {error && (
        <div style={{ color: 'red', marginBottom: '20px' }}>
          ❌ {error}
        </div>
      )}
      
      {/* 컨트롤 버튼 */}
      <div style={{ marginBottom: '20px' }}>
        <button 
          onClick={startRecording} 
          disabled={isRecording}
          style={{ marginRight: '10px' }}
        >
          녹음 시작
        </button>
        <button 
          onClick={stopRecording} 
          disabled={!isRecording}
          style={{ marginRight: '10px' }}
        >
          녹음 중지
        </button>
        <button onClick={clearTranscript}>
          내용 지우기
        </button>
      </div>
      
      {/* 전사 결과 */}
      <div style={{
        border: '1px solid #ccc',
        borderRadius: '5px',
        padding: '15px',
        minHeight: '200px',
        backgroundColor: '#f9f9f9',
        whiteSpace: 'pre-wrap'
      }}>
        {transcript || '전사 결과가 여기에 표시됩니다...'}
      </div>
    </div>
  );
}

export default STTComponent;
```

---

## 🎭 Vue.js 통합 예제

### 1. useSTT Composable

```javascript
// composables/useSTT.js
import { ref } from 'vue';

export function useSTT(wsUrl = 'ws://localhost:8003/ws/stt') {
  const transcript = ref('');
  const isRecording = ref(false);
  const isConnected = ref(false);
  const error = ref(null);
  
  let ws = null;
  let audioContext = null;
  let processor = null;
  let mediaStream = null;
  
  const startRecording = async () => {
    try {
      error.value = null;
      
      // WebSocket 연결
      ws = new WebSocket(wsUrl);
      
      ws.onopen = async () => {
        isConnected.value = true;
        
        // 마이크 권한 요청
        mediaStream = await navigator.mediaDevices.getUserMedia({
          audio: {
            sampleRate: 24000,
            channelCount: 1,
            echoCancellation: true,
            noiseSuppression: true
          }
        });
        
        // AudioContext 생성
        audioContext = new AudioContext({ sampleRate: 24000 });
        const source = audioContext.createMediaStreamSource(mediaStream);
        processor = audioContext.createScriptProcessor(4096, 1, 1);
        
        // 오디오 처리
        processor.onaudioprocess = (e) => {
          const inputData = e.inputBuffer.getChannelData(0);
          const pcm16 = new Int16Array(inputData.length);
          
          for (let i = 0; i < inputData.length; i++) {
            const s = Math.max(-1, Math.min(1, inputData[i]));
            pcm16[i] = s < 0 ? s * 0x8000 : s * 0x7FFF;
          }
          
          const base64 = btoa(String.fromCharCode.apply(null, new Uint8Array(pcm16.buffer)));
          
          if (ws?.readyState === WebSocket.OPEN) {
            ws.send(JSON.stringify({ type: 'audio', audio: base64 }));
          }
        };
        
        source.connect(processor);
        processor.connect(audioContext.destination);
        
        isRecording.value = true;
      };
      
      ws.onmessage = (event) => {
        const data = JSON.parse(event.data);
        
        if (data.type === 'transcript_completed') {
          transcript.value += data.text + '\n';
        } else if (data.type === 'error') {
          error.value = data.message;
        }
      };
      
      ws.onerror = (err) => {
        error.value = 'WebSocket 연결 오류';
        console.error(err);
      };
      
      ws.onclose = () => {
        isConnected.value = false;
        isRecording.value = false;
      };
      
    } catch (err) {
      error.value = err.message;
      console.error(err);
    }
  };
  
  const stopRecording = () => {
    if (ws?.readyState === WebSocket.OPEN) {
      ws.send(JSON.stringify({ type: 'stop' }));
    }
    
    // 리소스 정리
    processor?.disconnect();
    audioContext?.close();
    mediaStream?.getTracks().forEach(track => track.stop());
    ws?.close();
    
    isRecording.value = false;
  };
  
  const clearTranscript = () => {
    transcript.value = '';
  };
  
  return {
    transcript,
    isRecording,
    isConnected,
    error,
    startRecording,
    stopRecording,
    clearTranscript
  };
}
```

### 2. Vue 컴포넌트

```vue
<template>
  <div class="stt-container">
    <h1>🎤 실시간 음성 인식</h1>
    
    <!-- 상태 표시 -->
    <div class="status">
      상태: 
      <span v-if="isRecording">🔴 녹음 중</span>
      <span v-else-if="isConnected">🟢 연결됨</span>
      <span v-else>⚪ 연결 안됨</span>
    </div>
    
    <!-- 오류 표시 -->
    <div v-if="error" class="error">
      ❌ {{ error }}
    </div>
    
    <!-- 컨트롤 버튼 -->
    <div class="controls">
      <button @click="startRecording" :disabled="isRecording">
        녹음 시작
      </button>
      <button @click="stopRecording" :disabled="!isRecording">
        녹음 중지
      </button>
      <button @click="clearTranscript">
        내용 지우기
      </button>
    </div>
    
    <!-- 전사 결과 -->
    <div class="transcript">
      {{ transcript || '전사 결과가 여기에 표시됩니다...' }}
    </div>
  </div>
</template>

<script setup>
import { useSTT } from '@/composables/useSTT';

const {
  transcript,
  isRecording,
  isConnected,
  error,
  startRecording,
  stopRecording,
  clearTranscript
} = useSTT();
</script>

<style scoped>
.stt-container {
  padding: 20px;
}

.status {
  margin: 20px 0;
  font-size: 1.2em;
}

.error {
  color: red;
  margin: 20px 0;
}

.controls {
  margin: 20px 0;
}

.controls button {
  margin-right: 10px;
  padding: 10px 20px;
  font-size: 1em;
}

.transcript {
  border: 1px solid #ccc;
  border-radius: 5px;
  padding: 15px;
  min-height: 200px;
  background-color: #f9f9f9;
  white-space: pre-wrap;
}
</style>
```

---

## ❌ 오류 처리

### 일반적인 오류 및 해결 방법

```javascript
function handleError(error) {
  if (error instanceof DOMException) {
    switch (error.name) {
      case 'NotAllowedError':
        console.error('❌ 마이크 권한이 거부되었습니다.');
        alert('마이크 권한을 허용해주세요.');
        break;
        
      case 'NotFoundError':
        console.error('❌ 마이크를 찾을 수 없습니다.');
        alert('마이크가 연결되어 있는지 확인하세요.');
        break;
        
      case 'NotReadableError':
        console.error('❌ 마이크에 접근할 수 없습니다.');
        alert('다른 애플리케이션이 마이크를 사용 중일 수 있습니다.');
        break;
        
      default:
        console.error('❌ 알 수 없는 오류:', error);
        alert('오류가 발생했습니다: ' + error.message);
    }
  } else {
    console.error('❌ 오류:', error);
    alert('오류가 발생했습니다: ' + error.message);
  }
}
```

---

## ⚡ 성능 최적화

### 1. 오디오 버퍼 크기 조정

```javascript
// 낮은 지연시간 (더 많은 CPU 사용)
const processor = audioContext.createScriptProcessor(2048, 1, 1);

// 균형 (권장)
const processor = audioContext.createScriptProcessor(4096, 1, 1);

// 높은 처리량 (더 높은 지연시간)
const processor = audioContext.createScriptProcessor(8192, 1, 1);
```

### 2. 배치 전송

```javascript
let audioBuffer = [];
const BATCH_SIZE = 5;

processor.onaudioprocess = (e) => {
  const base64 = processAudio(e);
  audioBuffer.push(base64);
  
  // 5개씩 모아서 전송
  if (audioBuffer.length >= BATCH_SIZE) {
    ws.send(JSON.stringify({
      type: 'audio_batch',
      chunks: audioBuffer
    }));
    audioBuffer = [];
  }
};
```

### 3. Worker 사용

```javascript
// audio-worker.js
self.onmessage = (e) => {
  const { inputData } = e.data;
  
  // Float32 → Int16 변환
  const pcm16 = new Int16Array(inputData.length);
  for (let i = 0; i < inputData.length; i++) {
    const s = Math.max(-1, Math.min(1, inputData[i]));
    pcm16[i] = s < 0 ? s * 0x8000 : s * 0x7FFF;
  }
  
  // Base64 인코딩
  const base64 = btoa(String.fromCharCode.apply(null, new Uint8Array(pcm16.buffer)));
  
  self.postMessage({ base64 });
};
```

---

## ❓ FAQ

### Q1: 왜 샘플레이트가 반드시 24kHz여야 하나요?

**A**: OpenAI Realtime API의 요구사항입니다. 다른 샘플레이트를 사용하면 전사 품질이 저하되거나 오류가 발생할 수 있습니다.

### Q2: VAD를 비활성화하려면 어떻게 하나요?

**A**: 서버의 `.env` 파일에서 `VAD_ENABLED=false`로 설정하세요. VAD 비활성화 시 주기적으로 오디오를 커밋해야 합니다.

### Q3: HTTPS가 필요한가요?

**A**: 로컬 테스트(`localhost`)에서는 HTTP도 가능하지만, 프로덕션 환경에서는 HTTPS가 필수입니다.

### Q4: 모바일에서도 작동하나요?

**A**: 네, 모바일 브라우저(Chrome, Safari)에서도 작동합니다. 단, HTTPS 환경이어야 합니다.

### Q5: 여러 클라이언트가 동시에 연결할 수 있나요?

**A**: 네, 각 클라이언트는 독립적인 세션을 가집니다.

---

**문의사항이 있으면 팀에 연락하세요! 📞**

/**
 * STT 클라이언트 JavaScript
 * WebSocket 기반 실시간 음성 인식 클라이언트
 * 
 * @author Frontend Team
 * @version 1.0.0
 */

// ===========================
// 🌐 설정
// ===========================
const CONFIG = {
    // WebSocket 서버 주소 (환경에 맞게 수정)
    WS_URL: 'ws://localhost:8003/ws/stt',
    
    // 오디오 설정
    AUDIO: {
        sampleRate: 24000,      // 24kHz (Realtime API 필수)
        channelCount: 1,         // Mono
        echoCancellation: true,  // 에코 제거
        noiseSuppression: true   // 노이즈 제거
    },
    
    // 오디오 처리 설정
    BUFFER_SIZE: 4096,           // 오디오 버퍼 크기
};

// ===========================
// 📊 전역 변수
// ===========================
let ws = null;                   // WebSocket 연결
let audioContext = null;         // AudioContext
let mediaStream = null;          // MediaStream
let processor = null;            // ScriptProcessor
let isRecording = false;         // 녹음 상태
let transcriptCount = 0;         // 전사 완료 횟수
let audioChunkCount = 0;         // 전송된 오디오 청크 수
let sessionStartTime = null;     // 세션 시작 시각
let durationInterval = null;     // 지속 시간 업데이트 인터벌

// ===========================
// 🎨 UI 요소
// ===========================
const elements = {
    statusDot: document.getElementById('statusDot'),
    statusText: document.getElementById('statusText'),
    startBtn: document.getElementById('startBtn'),
    stopBtn: document.getElementById('stopBtn'),
    clearBtn: document.getElementById('clearBtn'),
    transcriptBox: document.getElementById('transcriptBox'),
    transcriptCount: document.getElementById('transcriptCount'),
    audioChunkCount: document.getElementById('audioChunkCount'),
    sessionDuration: document.getElementById('sessionDuration')
};

// ===========================
// 🎤 녹음 시작
// ===========================
async function startRecording() {
    try {
        updateStatus('연결 중...', 'connected');
        disableButton(elements.startBtn, true);
        
        // WebSocket 연결
        ws = new WebSocket(CONFIG.WS_URL);
        
        ws.onopen = async () => {
            console.log('✅ WebSocket 연결 성공');
            updateStatus('마이크 권한 요청 중...', 'connected');
            
            try {
                // 마이크 권한 요청
                mediaStream = await navigator.mediaDevices.getUserMedia({
                    audio: CONFIG.AUDIO
                });
                
                console.log('✅ 마이크 권한 허용됨');
                
                // AudioContext 생성
                audioContext = new AudioContext({ 
                    sampleRate: CONFIG.AUDIO.sampleRate 
                });
                
                const source = audioContext.createMediaStreamSource(mediaStream);
                processor = audioContext.createScriptProcessor(
                    CONFIG.BUFFER_SIZE, 
                    1,  // input channels
                    1   // output channels
                );
                
                // 오디오 데이터 처리
                processor.onaudioprocess = handleAudioProcess;
                
                source.connect(processor);
                processor.connect(audioContext.destination);
                
                // 녹음 시작
                isRecording = true;
                sessionStartTime = Date.now();
                transcriptCount = 0;
                audioChunkCount = 0;
                
                updateStatus('녹음 중...', 'recording');
                disableButton(elements.stopBtn, false);
                
                // 지속 시간 업데이트 시작
                startDurationUpdate();
                
                console.log('🎙️ 녹음 시작됨');
                
            } catch (error) {
                console.error('❌ 마이크 권한 오류:', error);
                alert('마이크 권한이 필요합니다.\n\n브라우저 설정에서 마이크 권한을 허용해주세요.');
                cleanup();
            }
        };
        
        ws.onmessage = handleWebSocketMessage;
        ws.onerror = handleWebSocketError;
        ws.onclose = handleWebSocketClose;
        
    } catch (error) {
        console.error('❌ 녹음 시작 오류:', error);
        alert('오류가 발생했습니다: ' + error.message);
        cleanup();
    }
}

// ===========================
// ⏹️ 녹음 중지
// ===========================
function stopRecording() {
    console.log('🛑 녹음 중지 요청');
    
    isRecording = false;
    
    // 서버에 중지 신호 전송
    if (ws && ws.readyState === WebSocket.OPEN) {
        ws.send(JSON.stringify({ type: 'stop' }));
        setTimeout(() => {
            ws.close();
        }, 500);
    }
    
    cleanup();
}

// ===========================
// 🗑️ 전사 내용 지우기
// ===========================
function clearTranscript() {
    elements.transcriptBox.innerHTML = '';
    console.log('🗑️ 전사 내용 삭제됨');
}

// ===========================
// 🎵 오디오 데이터 처리
// ===========================
function handleAudioProcess(e) {
    if (!isRecording || !ws || ws.readyState !== WebSocket.OPEN) {
        return;
    }
    
    try {
        // Float32Array 입력 데이터 가져오기
        const inputData = e.inputBuffer.getChannelData(0);
        
        // Int16Array로 변환 (PCM16 포맷)
        const pcm16 = new Int16Array(inputData.length);
        
        for (let i = 0; i < inputData.length; i++) {
            // -1.0 ~ 1.0 범위를 -32768 ~ 32767로 변환
            const s = Math.max(-1, Math.min(1, inputData[i]));
            pcm16[i] = s < 0 ? s * 0x8000 : s * 0x7FFF;
        }
        
        // Base64 인코딩
        const base64 = btoa(
            String.fromCharCode.apply(null, new Uint8Array(pcm16.buffer))
        );
        
        // WebSocket으로 전송
        ws.send(JSON.stringify({
            type: 'audio',
            audio: base64
        }));
        
        // 통계 업데이트
        audioChunkCount++;
        updateStats();
        
    } catch (error) {
        console.error('❌ 오디오 처리 오류:', error);
    }
}

// ===========================
// 📨 WebSocket 메시지 처리
// ===========================
function handleWebSocketMessage(event) {
    try {
        const data = JSON.parse(event.data);
        
        switch (data.type) {
            case 'transcript_delta':
                // 실시간 전사 (부분 결과)
                console.log('📝 [DELTA]', data.text);
                appendTranscript(data.text, 'delta');
                break;
                
            case 'transcript_completed':
                // 전사 완료 (최종 결과)
                console.log('✅ [COMPLETED]', data.text);
                appendTranscript('\n✅ ' + data.text + '\n', 'completed');
                transcriptCount++;
                updateStats();
                break;
                
            case 'speech_started':
                // 음성 감지 시작
                console.log('🎤 [음성 감지 시작]');
                appendTranscript('\n🎤 [음성 감지 시작]\n', 'event');
                break;
                
            case 'speech_stopped':
                // 음성 감지 종료
                console.log('⏸️ [음성 감지 종료]');
                appendTranscript('\n⏸️ [음성 감지 종료]\n', 'event');
                break;
                
            case 'error':
                // 오류
                console.error('❌ [오류]', data.message);
                appendTranscript('\n❌ 오류: ' + data.message + '\n', 'error');
                break;
                
            case 'info':
                // 정보
                console.log('ℹ️ [정보]', data.message);
                break;
                
            default:
                console.log('📨 [기타 메시지]', data.type);
        }
        
    } catch (error) {
        console.error('❌ 메시지 파싱 오류:', error);
    }
}

// ===========================
// 🔴 WebSocket 오류 처리
// ===========================
function handleWebSocketError(error) {
    console.error('❌ WebSocket 오류:', error);
    updateStatus('연결 오류', 'disconnected');
}

// ===========================
// 🔌 WebSocket 연결 종료 처리
// ===========================
function handleWebSocketClose() {
    console.log('🔌 WebSocket 연결 종료');
    updateStatus('연결 종료됨', 'disconnected');
    cleanup();
}

// ===========================
// 📝 전사 결과 추가
// ===========================
function appendTranscript(text, type = 'normal') {
    const entry = document.createElement('div');
    entry.className = 'log-entry';
    
    switch (type) {
        case 'delta':
            entry.classList.add('log-delta');
            entry.textContent = text;
            break;
        case 'completed':
            entry.classList.add('log-completed');
            entry.textContent = text;
            break;
        case 'event':
            entry.classList.add('log-event');
            entry.textContent = text;
            break;
        case 'error':
            entry.classList.add('log-error');
            entry.textContent = text;
            break;
        default:
            entry.textContent = text;
    }
    
    elements.transcriptBox.appendChild(entry);
    elements.transcriptBox.scrollTop = elements.transcriptBox.scrollHeight;
}

// ===========================
// 📊 통계 업데이트
// ===========================
function updateStats() {
    elements.transcriptCount.textContent = transcriptCount;
    elements.audioChunkCount.textContent = audioChunkCount;
}

// ===========================
// ⏱️ 지속 시간 업데이트
// ===========================
function startDurationUpdate() {
    durationInterval = setInterval(() => {
        if (sessionStartTime) {
            const elapsed = Math.floor((Date.now() - sessionStartTime) / 1000);
            elements.sessionDuration.textContent = elapsed + 's';
        }
    }, 1000);
}

function stopDurationUpdate() {
    if (durationInterval) {
        clearInterval(durationInterval);
        durationInterval = null;
    }
}

// ===========================
// 🎨 상태 업데이트
// ===========================
function updateStatus(text, className) {
    elements.statusText.textContent = text;
    elements.statusDot.className = 'status-dot status-' + className;
}

// ===========================
// 🔘 버튼 활성화/비활성화
// ===========================
function disableButton(button, disabled) {
    button.disabled = disabled;
}

// ===========================
// 🧹 리소스 정리
// ===========================
function cleanup() {
    isRecording = false;
    
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
        ws = null;
    }
    
    // UI 업데이트
    disableButton(elements.startBtn, false);
    disableButton(elements.stopBtn, true);
    updateStatus('연결되지 않음', 'disconnected');
    
    // 타이머 정리
    stopDurationUpdate();
    
    console.log('🧹 리소스 정리 완료');
}

// ===========================
// 🚀 초기화
// ===========================
console.log('🚀 STT 클라이언트 로드됨');
console.log('📍 WebSocket URL:', CONFIG.WS_URL);
console.log('🎤 오디오 설정:', CONFIG.AUDIO);

"""
STT FastAPI 서버
프론트엔드 팀 테스트용 실시간 음성 인식 서버
"""
import asyncio
import logging
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
import uvicorn

from config import HOST, PORT, VAD_ENABLED, LOG_LEVEL, WEBSOCKET_ENDPOINT
from stt_session import RealtimeSTTSession

# ===========================
# 📊 로깅 설정
# ===========================
logging.basicConfig(
    level=getattr(logging, LOG_LEVEL),
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

# ===========================
# 🚀 FastAPI 앱 생성
# ===========================
app = FastAPI(
    title="STT Server",
    description="실시간 음성 인식 서버 (OpenAI Realtime API)",
    version="1.0.0"
)

# ===========================
# 📄 루트 엔드포인트
# ===========================
@app.get("/")
async def root():
    """서버 상태 확인"""
    return {
        "status": "running",
        "message": "✅ STT 서버가 정상 작동 중입니다.",
        "endpoints": {
            "websocket": f"ws://{HOST}:{PORT}{WEBSOCKET_ENDPOINT}",
            "test_page": f"http://{HOST}:{PORT}/test"
        }
    }

# ===========================
# 🧪 테스트 페이지
# ===========================
@app.get("/test", response_class=HTMLResponse)
async def test_page():
    """간단한 테스트 페이지"""
    return """
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>STT 테스트</title>
    <style>
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            max-width: 800px;
            margin: 50px auto;
            padding: 20px;
            background: #f5f5f5;
        }
        .container {
            background: white;
            padding: 30px;
            border-radius: 10px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }
        h1 {
            color: #333;
            margin-bottom: 10px;
        }
        .status {
            padding: 10px;
            margin: 10px 0;
            border-radius: 5px;
            font-weight: bold;
        }
        .status.disconnected { background: #ffebee; color: #c62828; }
        .status.connected { background: #e8f5e9; color: #2e7d32; }
        .status.recording { background: #fff3e0; color: #e65100; }
        button {
            padding: 12px 24px;
            margin: 5px;
            border: none;
            border-radius: 5px;
            font-size: 16px;
            cursor: pointer;
            transition: all 0.3s;
        }
        button:hover { transform: translateY(-2px); }
        button:disabled { opacity: 0.5; cursor: not-allowed; }
        #startBtn { background: #4CAF50; color: white; }
        #stopBtn { background: #f44336; color: white; }
        #transcriptArea {
            width: 100%;
            height: 300px;
            margin-top: 20px;
            padding: 15px;
            border: 2px solid #ddd;
            border-radius: 5px;
            font-family: monospace;
            font-size: 14px;
            resize: vertical;
        }
        .info {
            background: #e3f2fd;
            padding: 15px;
            border-radius: 5px;
            margin: 20px 0;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>🎤 STT 서버 테스트</h1>
        <div id="statusDiv" class="status disconnected">🔴 연결되지 않음</div>
        
        <div style="margin: 20px 0;">
            <button id="startBtn" onclick="startRecording()">🎙️ 녹음 시작</button>
            <button id="stopBtn" onclick="stopRecording()" disabled>⏹️ 녹음 중지</button>
        </div>
        
        <div class="info">
            <strong>📋 사용 방법:</strong><br>
            1. "녹음 시작" 버튼을 클릭하세요<br>
            2. 마이크 권한을 허용하세요<br>
            3. 한국어로 말하세요<br>
            4. 실시간으로 전사 결과가 표시됩니다<br>
            5. 완료되면 "녹음 중지"를 클릭하세요
        </div>
        
        <textarea id="transcriptArea" readonly placeholder="전사 결과가 여기에 표시됩니다..."></textarea>
    </div>

    <script>
        let ws = null;
        let mediaRecorder = null;
        let audioContext = null;
        let isRecording = false;

        function updateStatus(text, className) {
            const statusDiv = document.getElementById('statusDiv');
            statusDiv.textContent = text;
            statusDiv.className = 'status ' + className;
        }

        function appendTranscript(text, isDelta = false) {
            const area = document.getElementById('transcriptArea');
            if (isDelta) {
                // 델타는 현재 줄에 추가
                const lines = area.value.split('\\n');
                lines[lines.length - 1] += text;
                area.value = lines.join('\\n');
            } else {
                // 완료된 전사는 새 줄로
                area.value += text + '\\n';
            }
            area.scrollTop = area.scrollHeight;
        }

        async function startRecording() {
            try {
                updateStatus('🔄 연결 중...', 'connected');
                
                // WebSocket 연결
                ws = new WebSocket(`ws://${window.location.host}/ws/stt`);
                
                ws.onopen = async () => {
                    updateStatus('🟢 연결됨 - 녹음 준비 중...', 'connected');
                    
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
                    audioContext = new AudioContext({ sampleRate: 24000 });
                    const source = audioContext.createMediaStreamSource(stream);
                    const processor = audioContext.createScriptProcessor(4096, 1, 1);
                    
                    processor.onaudioprocess = (e) => {
                        if (!isRecording) return;
                        
                        const inputData = e.inputBuffer.getChannelData(0);
                        const pcm16 = new Int16Array(inputData.length);
                        
                        for (let i = 0; i < inputData.length; i++) {
                            const s = Math.max(-1, Math.min(1, inputData[i]));
                            pcm16[i] = s < 0 ? s * 0x8000 : s * 0x7FFF;
                        }
                        
                        // Base64 인코딩
                        const base64 = btoa(String.fromCharCode.apply(null, new Uint8Array(pcm16.buffer)));
                        
                        // WebSocket으로 전송
                        if (ws && ws.readyState === WebSocket.OPEN) {
                            ws.send(JSON.stringify({
                                type: 'audio',
                                audio: base64
                            }));
                        }
                    };
                    
                    source.connect(processor);
                    processor.connect(audioContext.destination);
                    
                    isRecording = true;
                    updateStatus('🔴 녹음 중...', 'recording');
                    document.getElementById('startBtn').disabled = true;
                    document.getElementById('stopBtn').disabled = false;
                };
                
                ws.onmessage = (event) => {
                    const data = JSON.parse(event.data);
                    
                    if (data.type === 'transcript_delta') {
                        appendTranscript(data.text, true);
                    } else if (data.type === 'transcript_completed') {
                        appendTranscript('\\n✅ ' + data.text + '\\n');
                    } else if (data.type === 'error') {
                        appendTranscript('\\n❌ 오류: ' + data.message + '\\n');
                    } else if (data.type === 'speech_started') {
                        appendTranscript('\\n🎤 [음성 감지 시작]\\n');
                    } else if (data.type === 'speech_stopped') {
                        appendTranscript('\\n⏸️ [음성 감지 종료]\\n');
                    } else if (data.type === 'info') {
                        console.log('ℹ️', data.message);
                    }
                };
                
                ws.onerror = (error) => {
                    console.error('WebSocket 오류:', error);
                    updateStatus('❌ 연결 오류', 'disconnected');
                };
                
                ws.onclose = () => {
                    updateStatus('🔴 연결 종료됨', 'disconnected');
                    isRecording = false;
                    document.getElementById('startBtn').disabled = false;
                    document.getElementById('stopBtn').disabled = true;
                };
                
            } catch (error) {
                console.error('녹음 시작 오류:', error);
                alert('오류: ' + error.message);
                updateStatus('❌ 오류 발생', 'disconnected');
            }
        }

        function stopRecording() {
            isRecording = false;
            
            if (ws) {
                ws.send(JSON.stringify({ type: 'stop' }));
                setTimeout(() => ws.close(), 500);
            }
            
            if (audioContext) {
                audioContext.close();
                audioContext = null;
            }
            
            updateStatus('🟡 녹음 중지됨', 'connected');
            document.getElementById('startBtn').disabled = false;
            document.getElementById('stopBtn').disabled = true;
        }
    </script>
</body>
</html>
    """

# ===========================
# 🔌 WebSocket 엔드포인트
# ===========================
@app.websocket(WEBSOCKET_ENDPOINT)
async def websocket_stt(websocket: WebSocket):
    """
    실시간 음성 인식 WebSocket 엔드포인트
    
    메시지 형식:
    - 클라이언트 → 서버:
        {"type": "audio", "audio": "<base64-encoded-pcm16>"}
        {"type": "stop"}
    
    - 서버 → 클라이언트:
        {"type": "transcript_delta", "text": "...", "item_id": "...", "timestamp": "..."}
        {"type": "transcript_completed", "text": "...", "item_id": "...", "timestamp": "..."}
        {"type": "speech_started", "timestamp": "..."}
        {"type": "speech_stopped", "timestamp": "..."}
        {"type": "error", "message": "..."}
        {"type": "info", "message": "..."}
    """
    await websocket.accept()
    client_id = id(websocket)
    logger.info(f"✅ 클라이언트 연결됨 (ID: {client_id})")
    
    session = RealtimeSTTSession(websocket)
    chunk_count = 0
    
    try:
        # OpenAI Realtime API 연결
        if not await session.connect_to_openai():
            await websocket.send_json({
                "type": "error",
                "message": "OpenAI Realtime API 연결 실패"
            })
            return
        
        # OpenAI 이벤트 수신 태스크 시작
        listen_task = asyncio.create_task(session.listen_openai_events())
        
        # 클라이언트 메시지 수신
        while True:
            data = await websocket.receive_json()
            
            if data.get("type") == "audio":
                # 오디오 청크 전송
                audio_base64 = data.get("audio", "")
                
                if audio_base64:
                    chunk_count += 1
                    await session.send_audio(audio_base64)
                    
                    # VAD 미사용 시 주기적으로 커밋
                    if not VAD_ENABLED and chunk_count % 5 == 0:  # 1초마다 (200ms * 5)
                        await session.commit_audio()
            
            elif data.get("type") == "stop":
                logger.info(f"🛑 녹음 중지 요청 (클라이언트 {client_id})")
                
                # 마지막 오디오 커밋
                if not VAD_ENABLED:
                    await session.commit_audio()
                
                await websocket.send_json({
                    "type": "info",
                    "message": "✅ 녹음 종료"
                })
                break
                        
    except WebSocketDisconnect:
        logger.info(f"🔌 클라이언트 연결 끊김 (ID: {client_id})")
    except Exception as e:
        logger.error(f"❌ WebSocket 오류 (클라이언트 {client_id}): {e}", exc_info=True)
        try:
            await websocket.send_json({
                "type": "error",
                "message": f"서버 오류: {str(e)}"
            })
        except:
            pass
    finally:
        await session.close()
        if 'listen_task' in locals():
            listen_task.cancel()
        logger.info(f"🔚 세션 종료 (클라이언트 {client_id}, 총 {chunk_count}개 청크 처리)")


# ===========================
# 🏃 서버 실행
# ===========================
if __name__ == "__main__":
    logger.info("=" * 60)
    logger.info("🚀 STT 서버 시작")
    logger.info(f"📍 주소: http://{HOST}:{PORT}")
    logger.info(f"🔌 WebSocket: ws://{HOST}:{PORT}{WEBSOCKET_ENDPOINT}")
    logger.info(f"🧪 테스트 페이지: http://{HOST}:{PORT}/test")
    logger.info(f"🎯 VAD 활성화: {VAD_ENABLED}")
    logger.info("=" * 60)
    
    uvicorn.run(
        app,
        host=HOST,
        port=PORT,
        log_level=LOG_LEVEL.lower()
    )

"""
OpenAI Realtime API 세션 관리
실시간 음성 인식 세션 및 이벤트 처리
"""
import json
import time
import asyncio
import logging
from typing import Optional
from datetime import datetime
from fastapi import WebSocket
import websockets
from websockets.client import WebSocketClientProtocol

from config import (
    OPENAI_API_KEY,
    REALTIME_API_URL,
    TRANSCRIPTION_MODEL,
    LANGUAGE,
    VAD_ENABLED,
    VAD_THRESHOLD,
    VAD_PREFIX_PADDING_MS,
    VAD_SILENCE_DURATION_MS
)

logger = logging.getLogger(__name__)


class RealtimeSTTSession:
    """OpenAI Realtime API 세션 관리"""
    
    def __init__(self, client_ws: WebSocket):
        self.client_ws = client_ws
        self.openai_ws: Optional[WebSocketClientProtocol] = None
        self.is_connected = False
        self.session_id = None
        self.heartbeat_task = None
        
        # 📊 성능 측정 변수
        self.first_audio_time = None  # 첫 오디오 전송 시각
        self.first_response_time = None  # 첫 전사 델타 수신 시각
        self.last_audio_time = None  # 마지막 오디오 전송 시각
        self.transcripts = []  # 전사 완료 이벤트 기록 (시각, 텍스트)
        
    async def connect_to_openai(self):
        """OpenAI Realtime API에 연결"""
        try:
            headers = [
                ("Authorization", f"Bearer {OPENAI_API_KEY}"),
                ("OpenAI-Beta", "realtime=v1")
            ]
            
            self.openai_ws = await websockets.connect(
                REALTIME_API_URL,
                additional_headers=headers,
                ping_interval=20,  # 20초마다 ping
                ping_timeout=10
            )
            
            self.is_connected = True
            logger.info("✅ OpenAI Realtime API 연결 성공")
            
            # 세션 설정
            await self.configure_session()
            
            # heartbeat 시작
            self.heartbeat_task = asyncio.create_task(self.heartbeat())
            
            return True
            
        except Exception as e:
            logger.error(f"❌ OpenAI Realtime API 연결 실패: {e}")
            return False
    
    async def configure_session(self):
        """세션 설정 (한국어, VAD 등)"""
        config = {
            "type": "session.update",
            "session": {
                "modalities": ["text"],  # 🔥 오디오 출력 비활성화 (비용 절감)
                "instructions": "당신은 한국어 음성 인식 전문가입니다. 정확하게 한국어 음성을 텍스트로 변환하세요.",
                "input_audio_format": "pcm16",
                "input_audio_transcription": {
                    "model": TRANSCRIPTION_MODEL,
                    "language": LANGUAGE
                },
                "turn_detection": {
                    "type": "server_vad",
                    "threshold": VAD_THRESHOLD,
                    "prefix_padding_ms": VAD_PREFIX_PADDING_MS,
                    "silence_duration_ms": VAD_SILENCE_DURATION_MS
                } if VAD_ENABLED else None,
                "temperature": 0.6,  # Realtime API 최소값
            }
        }
        
        await self.openai_ws.send(json.dumps(config))
        logger.info(f"⚙️ 세션 설정 완료 (언어: {LANGUAGE}, VAD: {VAD_ENABLED}, 오디오출력: OFF)")
    
    async def heartbeat(self):
        """주기적인 heartbeat 전송"""
        while self.is_connected:
            try:
                await asyncio.sleep(20)  # 20초마다
                if self.openai_ws and self.is_connected:
                    await self.openai_ws.ping()
                    logger.debug("💓 Heartbeat sent")
            except Exception as e:
                logger.error(f"❌ Heartbeat 오류: {e}")
                break
    
    async def send_audio(self, audio_base64: str):
        """오디오 청크 전송"""
        if not self.openai_ws or not self.is_connected:
            return
            
        try:
            # 📊 첫 오디오 전송 시각 기록
            if self.first_audio_time is None:
                self.first_audio_time = time.time()
                logger.info("🎤 첫 오디오 청크 전송 시작")
            
            self.last_audio_time = time.time()
            
            event = {
                "type": "input_audio_buffer.append",
                "audio": audio_base64
            }
            await self.openai_ws.send(json.dumps(event))
            logger.debug("📤 오디오 청크 전송")
            
        except Exception as e:
            logger.error(f"❌ 오디오 전송 오류: {e}")
    
    async def commit_audio(self):
        """오디오 버퍼 커밋 (VAD 미사용 시)"""
        if not self.openai_ws or not self.is_connected:
            return
            
        try:
            event = {
                "type": "input_audio_buffer.commit"
            }
            await self.openai_ws.send(json.dumps(event))
            logger.debug("✅ 오디오 버퍼 커밋")
            
        except Exception as e:
            logger.error(f"❌ 오디오 커밋 오류: {e}")
    
    async def listen_openai_events(self):
        """OpenAI 이벤트 수신 및 처리"""
        try:
            async for message in self.openai_ws:
                try:
                    event = json.loads(message)
                    await self.handle_openai_event(event)
                except json.JSONDecodeError as e:
                    logger.error(f"❌ JSON 파싱 오류: {e}")
                except Exception as e:
                    logger.error(f"❌ 이벤트 처리 오류: {e}")
                    
        except websockets.exceptions.ConnectionClosed:
            logger.info("🔌 OpenAI 연결 종료")
        except Exception as e:
            logger.error(f"❌ 이벤트 수신 오류: {e}")
        finally:
            self.is_connected = False
    
    async def handle_openai_event(self, event: dict):
        """OpenAI 이벤트 처리"""
        event_type = event.get("type")
        
        if event_type == "session.created":
            self.session_id = event.get("session", {}).get("id")
            logger.info(f"🎉 세션 생성됨: {self.session_id}")
            await self.client_ws.send_json({
                "type": "info",
                "message": f"✅ Realtime API 연결 완료 (세션: {self.session_id})"
            })
        
        elif event_type == "session.updated":
            logger.info("⚙️ 세션 업데이트됨")
        
        elif event_type == "conversation.item.input_audio_transcription.delta":
            # 실시간 전사 델타 (부분 결과)
            delta = event.get("delta", "")
            transcript_id = event.get("item_id", "")
            
            # 📊 첫 응답 시간 측정
            if delta and self.first_response_time is None and self.first_audio_time is not None:
                self.first_response_time = time.time()
                latency = self.first_response_time - self.first_audio_time
                logger.info(f"⚡ 첫 응답 지연시간: {latency:.2f}초 (첫 오디오 → 첫 델타)")
            
            if delta:
                logger.info(f"📝 [DELTA] {delta}")
                await self.client_ws.send_json({
                    "type": "transcript_delta",
                    "text": delta,
                    "item_id": transcript_id,
                    "timestamp": datetime.utcnow().isoformat()
                })
        
        elif event_type == "conversation.item.input_audio_transcription.completed":
            # 전사 완료 (최종 결과)
            transcript = event.get("transcript", "")
            transcript_id = event.get("item_id", "")
            
            if transcript:
                # 📊 전사 완료 시간 기록
                completion_time = time.time()
                self.transcripts.append({
                    "time": completion_time,
                    "text": transcript,
                    "id": transcript_id
                })
                
                # 발화 후 전사까지 걸린 시간 (마지막 오디오 기준)
                if self.last_audio_time:
                    time_since_last_audio = completion_time - self.last_audio_time
                    logger.info(f"⏱️  발화 종료 → 전사 완료: {time_since_last_audio:.2f}초")
                
                # 평균 전사 시간 계산
                if len(self.transcripts) >= 2:
                    intervals = []
                    for i in range(1, len(self.transcripts)):
                        interval = self.transcripts[i]["time"] - self.transcripts[i-1]["time"]
                        intervals.append(interval)
                    avg_interval = sum(intervals) / len(intervals)
                    logger.info(f"📊 평균 전사 간격: {avg_interval:.2f}초 (전사 {len(self.transcripts)}개)")
                
                logger.info(f"✅ [COMPLETED] {transcript}")
                await self.client_ws.send_json({
                    "type": "transcript_completed",
                    "text": transcript,
                    "item_id": transcript_id,
                    "timestamp": datetime.utcnow().isoformat()
                })
        
        elif event_type == "conversation.item.input_audio_transcription.failed":
            error = event.get("error", {})
            logger.error(f"❌ 전사 실패: {error}")
            await self.client_ws.send_json({
                "type": "error",
                "message": f"전사 실패: {error.get('message', '알 수 없는 오류')}"
            })
        
        elif event_type == "input_audio_buffer.speech_started":
            logger.info("🎤 음성 감지 시작 (VAD)")
            await self.client_ws.send_json({
                "type": "speech_started",
                "timestamp": datetime.utcnow().isoformat()
            })
        
        elif event_type == "input_audio_buffer.speech_stopped":
            logger.info("⏸️ 음성 감지 종료 (VAD)")
            
            # 📊 음성 종료 시 성능 요약 출력
            if self.first_audio_time and self.last_audio_time:
                total_duration = self.last_audio_time - self.first_audio_time
                logger.info(f"📊 === 음성 세그먼트 성능 요약 ===")
                logger.info(f"  📍 총 발화 시간: {total_duration:.2f}초")
                if self.first_response_time:
                    logger.info(f"  ⚡ 첫 응답 지연: {self.first_response_time - self.first_audio_time:.2f}초")
                logger.info(f"  📝 전사 횟수: {len(self.transcripts)}개")
                logger.info(f"📊 ============================")
            
            await self.client_ws.send_json({
                "type": "speech_stopped",
                "timestamp": datetime.utcnow().isoformat()
            })
        
        elif event_type == "input_audio_buffer.committed":
            logger.debug("✅ 오디오 버퍼 커밋됨")
        
        elif event_type == "error":
            error = event.get("error", {})
            logger.error(f"❌ OpenAI 오류: {error}")
            await self.client_ws.send_json({
                "type": "error",
                "message": f"OpenAI 오류: {error.get('message', '알 수 없는 오류')}"
            })
        
        else:
            logger.debug(f"📨 기타 이벤트: {event_type}")
    
    async def close(self):
        """연결 종료"""
        self.is_connected = False
        
        if self.heartbeat_task:
            self.heartbeat_task.cancel()
        
        if self.openai_ws:
            await self.openai_ws.close()
            logger.info("🔌 OpenAI 연결 종료됨")

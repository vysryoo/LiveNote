package com.capstone.livenote.recording;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.ArgumentCaptor;
import org.mockito.Mock;
import org.mockito.junit.jupiter.MockitoExtension;
import org.mockito.junit.jupiter.MockitoSettings;
import org.mockito.quality.Strictness;
import org.springframework.web.socket.TextMessage;
import org.springframework.web.socket.WebSocketSession;

import java.net.http.WebSocket;
import java.util.List;

import static org.assertj.core.api.Assertions.assertThat;
import static org.mockito.ArgumentMatchers.*;
import static org.mockito.Mockito.*;

/**
 * OpenAI 이벤트를 차례로 넣어 전사 저장 시각, 브라우저 메시지, 녹음 정지 후 처리를 확인한다.
 */
@ExtendWith(MockitoExtension.class)
@MockitoSettings(strictness = Strictness.LENIENT)
class OpenAiTranscriptionSessionTest {

    private static final long LECTURE = 4L;
    // 강의를 재개한 경우 이전 녹음의 마지막 시각(초)
    private static final int RESUME_FROM = 100;
    // PCM16, 24kHz, 모노 음성 1초 분량
    private static final int ONE_SECOND = 24000 * 2;
    private static final ObjectMapper MAPPER = new ObjectMapper();

    @Mock WebSocketSession client;
    @Mock WebSocket openAi;
    @Mock TranscriptService transcriptService;

    private OpenAiTranscriptionSession session;

    @BeforeEach
    void setUp() {
        when(client.isOpen()).thenReturn(true);
        session = new OpenAiTranscriptionSession(client, LECTURE, "ko", RESUME_FROM,
                new ObjectMapper(), transcriptService, "gpt-transcribe");
    }

    @Test
    void completedSpeech_savedWithLectureTimeAndSentAsFinal() throws Exception {
        session.onOpenAiConnected(openAi);

        speak("a", 2000, 4500, "스택은 후입선출이다");

        verify(transcriptService).saveFromStt(LECTURE, 102, 105, "스택은 후입선출이다");
        assertThat(clientMessages()).containsExactly(
                json("{\"type\":\"transcript\",\"data\":{\"content\":\"스택은 후입선출이다\",\"isFinal\":true}}"));
    }

    @Test
    void nextSpeech_neverStartsBeforePreviousEnd() {
        session.onOpenAiConnected(openAi);

        speak("a", 2000, 4500, "첫 문장");
        speak("b", 4000, 6000, "둘째 문장");

        verify(transcriptService).saveFromStt(LECTURE, 105, 106, "둘째 문장");
    }

    @Test
    void speechWithoutStopEvent_endsAtSentAudioLength() {
        session.onOpenAiConnected(openAi);
        session.appendAudio(new byte[ONE_SECOND * 3]);

        session.handleEvent(event("input_audio_buffer.speech_started", "\"item_id\":\"a\",\"audio_start_ms\":1000"));
        session.handleEvent(event("input_audio_buffer.committed", "\"item_id\":\"a\""));
        session.handleEvent(event("conversation.item.input_audio_transcription.completed", "\"item_id\":\"a\",\"transcript\":\"끝\""));

        verify(transcriptService).saveFromStt(LECTURE, 101, 103, "끝");
    }

    @Test
    void delta_sentAsPartialWithoutSaving() throws Exception {
        session.onOpenAiConnected(openAi);

        session.handleEvent(event("conversation.item.input_audio_transcription.delta", "\"item_id\":\"a\",\"delta\":\"스택\""));
        session.handleEvent(event("conversation.item.input_audio_transcription.delta", "\"item_id\":\"a\",\"delta\":\"은\""));

        assertThat(clientMessages()).containsExactly(
                json("{\"type\":\"transcript\",\"data\":{\"content\":\"스택\",\"isFinal\":false}}"),
                json("{\"type\":\"transcript\",\"data\":{\"content\":\"스택은\",\"isFinal\":false}}"));
        verifyNoInteractions(transcriptService);
    }

    @Test
    void audioBeforeConnection_sentAfterConnected() {
        session.appendAudio(new byte[]{1, 2});
        verifyNoInteractions(openAi);

        session.onOpenAiConnected(openAi);

        verify(openAi).sendText(argThat(text -> text.toString().contains("input_audio_buffer.append")), eq(true));
    }

    @Test
    void stopWhileSpeaking_commitsAndClosesAfterLastTranscript() {
        session.onOpenAiConnected(openAi);
        session.handleEvent(event("input_audio_buffer.speech_started", "\"item_id\":\"a\",\"audio_start_ms\":0"));

        when(client.isOpen()).thenReturn(false);
        session.finishAfterClientClosed();

        verify(openAi).sendText("{\"type\":\"input_audio_buffer.commit\"}", true);
        verify(openAi, never()).sendClose(anyInt(), anyString());

        session.handleEvent(event("input_audio_buffer.committed", "\"item_id\":\"a\""));
        session.handleEvent(event("conversation.item.input_audio_transcription.completed", "\"item_id\":\"a\",\"transcript\":\"마지막\""));

        // 브라우저 연결은 닫혔으므로 저장만 하고, 남은 전사가 없으니 OpenAI 연결을 닫음
        verify(transcriptService).saveFromStt(eq(LECTURE), anyInt(), anyInt(), eq("마지막"));
        verify(openAi).sendClose(WebSocket.NORMAL_CLOSURE, "client closed");
    }

    @Test
    void stopWhenIdle_closesImmediately() {
        session.onOpenAiConnected(openAi);

        session.finishAfterClientClosed();

        verify(openAi, never()).sendText(contains("commit"), anyBoolean());
        verify(openAi).sendClose(WebSocket.NORMAL_CLOSURE, "client closed");
    }

    @Test
    void commitErrorAfterStop_stopsWaiting() {
        session.onOpenAiConnected(openAi);
        session.handleEvent(event("input_audio_buffer.speech_started", "\"item_id\":\"a\",\"audio_start_ms\":0"));
        when(client.isOpen()).thenReturn(false);
        session.finishAfterClientClosed();

        session.handleEvent("{\"type\":\"error\",\"error\":{\"message\":\"buffer too small\"}}");

        verify(openAi).sendClose(WebSocket.NORMAL_CLOSURE, "client closed");
    }

    private void speak(String item, int startMs, int endMs, String text) {
        session.handleEvent(event("input_audio_buffer.speech_started", "\"item_id\":\"" + item + "\",\"audio_start_ms\":" + startMs));
        session.handleEvent(event("input_audio_buffer.speech_stopped", "\"item_id\":\"" + item + "\",\"audio_end_ms\":" + endMs));
        session.handleEvent(event("input_audio_buffer.committed", "\"item_id\":\"" + item + "\""));
        session.handleEvent(event("conversation.item.input_audio_transcription.completed",
                "\"item_id\":\"" + item + "\",\"transcript\":\"" + text + "\""));
    }

    private static String event(String type, String fields) {
        return "{\"type\":\"" + type + "\"," + fields + "}";
    }

    // 메시지를 Map으로 만들어 키 순서가 정해져 있지 않으므로 JSON 구조로 비교
    private List<JsonNode> clientMessages() throws Exception {
        ArgumentCaptor<TextMessage> messages = ArgumentCaptor.forClass(TextMessage.class);
        verify(client, atLeast(0)).sendMessage(messages.capture());
        return messages.getAllValues().stream().map(message -> json(message.getPayload())).toList();
    }

    private static JsonNode json(String text) {
        try {
            return MAPPER.readTree(text);
        } catch (Exception e) {
            throw new IllegalArgumentException(e);
        }
    }
}

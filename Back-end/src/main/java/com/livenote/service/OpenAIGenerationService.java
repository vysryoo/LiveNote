package com.livenote.service;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import lombok.extern.slf4j.Slf4j;
import okhttp3.*;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Service;

import java.io.IOException;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.concurrent.TimeUnit;

@Slf4j
@Service
public class OpenAIGenerationService {
    private static final String CHAT_API_URL = "https://api.openai.com/v1/chat/completions";
    
    @Value("${openai.api-key}")
    private String apiKey;
    
    @Value("${openai.chat-model:gpt-4o-mini}")
    private String model;
    
    private final ObjectMapper objectMapper;
    private final OkHttpClient httpClient;

    public OpenAIGenerationService(ObjectMapper objectMapper) {
        this.objectMapper = objectMapper;
        this.httpClient = new OkHttpClient.Builder()
                .connectTimeout(30, TimeUnit.SECONDS)
                .readTimeout(60, TimeUnit.SECONDS)
                .writeTimeout(30, TimeUnit.SECONDS)
                .build();
    }

    public String generateSummary(String transcriptText, String language) {
        try {
            String systemPrompt = language.contains("한국어") || language.contains("ko") 
                ? "당신은 강의 내용을 요약하는 전문가입니다. 주어진 전사 내용을 간결하고 명확하게 요약해주세요. 핵심 내용만 포함하고, 불필요한 세부사항은 제외하세요."
                : "You are an expert at summarizing lecture content. Summarize the given transcript concisely and clearly. Include only key points and exclude unnecessary details.";
            
            String userPrompt = language.contains("한국어") || language.contains("ko")
                ? "다음 강의 전사 내용을 요약해주세요:\n\n" + transcriptText
                : "Please summarize the following lecture transcript:\n\n" + transcriptText;

            String response = callOpenAI(systemPrompt, userPrompt);
            return response;
        } catch (Exception e) {
            log.error("요약 생성 실패", e);
            throw new RuntimeException("요약 생성 실패: " + e.getMessage(), e);
        }
    }

    public List<Map<String, Object>> generateQnA(String transcriptText, String language) {
        try {
            String systemPrompt = language.contains("한국어") || language.contains("ko")
                ? "당신은 강의 내용을 바탕으로 학습 질문을 생성하는 전문가입니다. 개념 이해, 응용, 심화, 비교 등 다양한 유형의 질문과 답변을 생성해주세요. 각 질문은 JSON 형식으로 제공해주세요."
                : "You are an expert at generating learning questions based on lecture content. Generate various types of questions and answers including concept understanding, application, advanced, and comparison. Provide each question in JSON format.";
            
            String userPrompt = language.contains("한국어") || language.contains("ko")
                ? "다음 강의 전사 내용을 바탕으로 학습에 도움이 되는 질문 4개와 답변을 생성해주세요. 각 질문은 서로 다른 유형이어야 합니다:\n" +
                  "- concept (개념 확인): 기본 개념을 이해하는 질문\n" +
                  "- application (응용 확장): 개념을 실제 상황에 적용하는 질문\n" +
                  "- advanced (심화 질의): 심화된 내용을 다루는 질문\n" +
                  "- comparison (비교 분석): 다른 개념과 비교하는 질문\n\n" +
                  "각 질문은 다음 JSON 형식으로 제공해주세요:\n" +
                  "{\"type\": \"concept|application|advanced|comparison\", \"question\": \"질문 내용\", \"answer\": \"답변 내용\"}\n\n" +
                  "전사 내용:\n" + transcriptText
                : "Based on the following lecture transcript, generate 4 helpful learning questions and answers. Each question must be a different type:\n" +
                  "- concept: Questions that test understanding of basic concepts\n" +
                  "- application: Questions that apply concepts to real situations\n" +
                  "- advanced: Questions that cover advanced content\n" +
                  "- comparison: Questions that compare different concepts\n\n" +
                  "Provide each question in the following JSON format:\n" +
                  "{\"type\": \"concept|application|advanced|comparison\", \"question\": \"question text\", \"answer\": \"answer text\"}\n\n" +
                  "Transcript:\n" + transcriptText;

            log.info("QnA 생성 시작: transcriptLength={}, language={}", transcriptText.length(), language);
            String response = callOpenAI(systemPrompt, userPrompt);
            log.info("OpenAI API 응답 수신: responseLength={}, responsePreview={}", 
                response != null ? response.length() : 0, 
                response != null && response.length() > 100 ? response.substring(0, 100) : response);
            
            List<Map<String, Object>> qnaList = parseQnAResponse(response);
            log.info("QnA 파싱 결과: qnaListSize={}", qnaList != null ? qnaList.size() : 0);
            
            if (qnaList == null || qnaList.isEmpty()) {
                log.error("QnA 파싱 결과가 비어있음: response={}", response);
                throw new RuntimeException("QnA 파싱 결과가 비어있습니다. OpenAI 응답: " + (response != null && response.length() > 200 ? response.substring(0, 200) : response));
            }
            
            return qnaList;
        } catch (Exception e) {
            log.error("질문 생성 실패: transcriptLength={}", transcriptText != null ? transcriptText.length() : 0, e);
            throw new RuntimeException("질문 생성 실패: " + e.getMessage(), e);
        }
    }

    public List<Map<String, Object>> generateResources(String transcriptText, String language) {
        try {
            String systemPrompt = language.contains("한국어") || language.contains("ko")
                ? "당신은 강의 내용과 관련된 학습 자료를 추천하는 전문가입니다. 논문, 위키피디아, 동영상, 블로그 등 다양한 유형의 자료를 추천해주세요. 각 자료는 JSON 형식으로 제공해주세요."
                : "You are an expert at recommending learning resources related to lecture content. Recommend various types of resources including papers, Wikipedia, videos, and blogs. Provide each resource in JSON format.";
            
            String userPrompt = language.contains("한국어") || language.contains("ko")
                ? "다음 강의 전사 내용과 관련된 학습 자료 4개를 추천해주세요. 각 자료는 서로 다른 소스여야 합니다:\n" +
                  "- paper (학술자료): 논문, 학술 자료\n" +
                  "- wiki (위키): 위키피디아 등 백과사전 자료\n" +
                  "- video (유튜브): 동영상 자료\n" +
                  "- blog (웹): 블로그, 웹사이트 자료\n\n" +
                  "각 자료는 다음 JSON 형식으로 제공해주세요:\n" +
                  "{\"type\": \"paper|wiki|video|blog\", \"title\": \"자료 제목\", \"text\": \"자료 설명\", \"url\": \"URL (없으면 null)\", \"thumbnail\": \"썸네일 URL (없으면 null)\", \"score\": 0.9}\n\n" +
                  "전사 내용:\n" + transcriptText
                : "Recommend 4 learning resources related to the following lecture transcript. Each resource must be from a different source:\n" +
                  "- paper: Academic papers and scholarly materials\n" +
                  "- wiki: Wikipedia and encyclopedia materials\n" +
                  "- video: Video materials\n" +
                  "- blog: Blog and website materials\n\n" +
                  "Provide each resource in the following JSON format:\n" +
                  "{\"type\": \"paper|wiki|video|blog\", \"title\": \"resource title\", \"text\": \"resource description\", \"url\": \"URL (null if not available)\", \"thumbnail\": \"thumbnail URL (null if not available)\", \"score\": 0.9}\n\n" +
                  "Transcript:\n" + transcriptText;

            String response = callOpenAI(systemPrompt, userPrompt);
            return parseResourcesResponse(response);
        } catch (Exception e) {
            log.error("자료 추천 생성 실패", e);
            throw new RuntimeException("자료 추천 생성 실패: " + e.getMessage(), e);
        }
    }

    private String callOpenAI(String systemPrompt, String userPrompt) throws IOException {
        Map<String, Object> requestBody = new HashMap<>();
        requestBody.put("model", model);
        
        List<Map<String, String>> messages = new ArrayList<>();
        Map<String, String> systemMessage = new HashMap<>();
        systemMessage.put("role", "system");
        systemMessage.put("content", systemPrompt);
        messages.add(systemMessage);
        
        Map<String, String> userMessage = new HashMap<>();
        userMessage.put("role", "user");
        userMessage.put("content", userPrompt);
        messages.add(userMessage);
        
        requestBody.put("messages", messages);
        requestBody.put("temperature", 0.7);
        requestBody.put("max_tokens", 2000);

        String jsonBody = objectMapper.writeValueAsString(requestBody);
        
        RequestBody body = RequestBody.create(
            jsonBody,
            MediaType.get("application/json; charset=utf-8")
        );
        
        Request request = new Request.Builder()
                .url(CHAT_API_URL)
                .addHeader("Authorization", "Bearer " + apiKey)
                .addHeader("Content-Type", "application/json")
                .post(body)
                .build();

        try (Response response = httpClient.newCall(request).execute()) {
            if (!response.isSuccessful()) {
                String errorBody = response.body() != null ? response.body().string() : "Unknown error";
                log.error("OpenAI API 호출 실패: code={}, body={}", response.code(), errorBody);
                throw new RuntimeException("OpenAI API 호출 실패: " + response.code() + " - " + errorBody);
            }
            
            String responseBody = response.body().string();
            log.debug("OpenAI API 응답 수신: responseBodyLength={}", responseBody.length());
            
            JsonNode jsonResponse = objectMapper.readTree(responseBody);
            
            if (jsonResponse.has("choices") && jsonResponse.get("choices").isArray() 
                && jsonResponse.get("choices").size() > 0) {
                JsonNode choice = jsonResponse.get("choices").get(0);
                if (choice.has("message") && choice.get("message").has("content")) {
                    String content = choice.get("message").get("content").asText();
                    log.debug("OpenAI API 응답 내용 추출: contentLength={}", content.length());
                    if (content == null || content.trim().isEmpty()) {
                        log.error("OpenAI API 응답 내용이 비어있음: responseBody={}", responseBody.length() > 500 ? responseBody.substring(0, 500) + "..." : responseBody);
                        throw new RuntimeException("OpenAI API 응답 내용이 비어있습니다");
                    }
                    return content;
                } else {
                    log.error("OpenAI 응답에 content 필드 없음: choice={}", choice.toString());
                }
            } else {
                log.error("OpenAI 응답에 choices 배열 없음 또는 비어있음: responseBody={}", responseBody.length() > 500 ? responseBody.substring(0, 500) + "..." : responseBody);
            }
            
            throw new RuntimeException("OpenAI 응답 형식 오류: " + (responseBody.length() > 500 ? responseBody.substring(0, 500) + "..." : responseBody));
        }
    }

    private List<Map<String, Object>> parseQnAResponse(String response) {
        List<Map<String, Object>> qnaList = new ArrayList<>();
        
        if (response == null || response.trim().isEmpty()) {
            log.error("QnA 응답이 null이거나 비어있음");
            return qnaList;
        }
        
        try {
            log.debug("QnA 응답 파싱 시작: response={}", response.length() > 500 ? response.substring(0, 500) + "..." : response);
            
            // 마크다운 코드 블록 제거 (```json ... ``` 형식)
            String cleanedResponse = response.trim();
            if (cleanedResponse.startsWith("```")) {
                // ```json 또는 ```로 시작하는 경우
                int startIndex = cleanedResponse.indexOf("\n");
                if (startIndex > 0) {
                    cleanedResponse = cleanedResponse.substring(startIndex + 1);
                }
                // 마지막 ``` 제거
                int lastIndex = cleanedResponse.lastIndexOf("```");
                if (lastIndex > 0) {
                    cleanedResponse = cleanedResponse.substring(0, lastIndex).trim();
                }
                log.debug("마크다운 코드 블록 제거 완료");
            }
            
            // JSON 배열 형식으로 파싱 시도
            if (cleanedResponse.trim().startsWith("[")) {
                JsonNode jsonArray = objectMapper.readTree(cleanedResponse);
                log.debug("JSON 배열 형식으로 파싱: 배열 크기={}", jsonArray.size());
                for (JsonNode item : jsonArray) {
                    Map<String, Object> qna = new HashMap<>();
                    qna.put("type", item.has("type") ? item.get("type").asText() : "concept");
                    qna.put("question", item.has("question") ? item.get("question").asText() : "");
                    qna.put("answer", item.has("answer") ? item.get("answer").asText() : "");
                    qnaList.add(qna);
                    log.debug("QnA 항목 추가: type={}, questionLength={}", qna.get("type"), ((String)qna.get("question")).length());
                }
            } else {
                // 텍스트에서 JSON 객체 추출 시도
                log.debug("텍스트에서 JSON 객체 추출 시도");
                String[] lines = cleanedResponse.split("\n");
                int foundCount = 0;
                for (String line : lines) {
                    line = line.trim();
                    if (line.startsWith("{") && line.endsWith("}")) {
                        try {
                            JsonNode item = objectMapper.readTree(line);
                            Map<String, Object> qna = new HashMap<>();
                            qna.put("type", item.has("type") ? item.get("type").asText() : "concept");
                            qna.put("question", item.has("question") ? item.get("question").asText() : "");
                            qna.put("answer", item.has("answer") ? item.get("answer").asText() : "");
                            qnaList.add(qna);
                            foundCount++;
                            log.debug("QnA 항목 추가 (텍스트에서): type={}, questionLength={}", qna.get("type"), ((String)qna.get("question")).length());
                        } catch (Exception e) {
                            log.warn("JSON 파싱 실패: {}", line, e);
                        }
                    }
                }
                log.debug("텍스트에서 찾은 JSON 객체 수: {}", foundCount);
            }
            
            if (qnaList.isEmpty()) {
                log.warn("QnA 파싱 결과가 비어있음. 원본 응답: {}", response.length() > 500 ? response.substring(0, 500) + "..." : response);
            }
        } catch (Exception e) {
            log.error("QnA 응답 파싱 실패: response={}", response.length() > 500 ? response.substring(0, 500) + "..." : response, e);
            // 기본값 반환하지 않음 (빈 리스트 반환하여 상위에서 에러 처리)
        }
        return qnaList;
    }

    private List<Map<String, Object>> parseResourcesResponse(String response) {
        List<Map<String, Object>> resourcesList = new ArrayList<>();
        try {
            // 마크다운 코드 블록 제거 (```json ... ``` 형식)
            String cleanedResponse = response != null ? response.trim() : "";
            if (cleanedResponse.startsWith("```")) {
                // ```json 또는 ```로 시작하는 경우
                int startIndex = cleanedResponse.indexOf("\n");
                if (startIndex > 0) {
                    cleanedResponse = cleanedResponse.substring(startIndex + 1);
                }
                // 마지막 ``` 제거
                int lastIndex = cleanedResponse.lastIndexOf("```");
                if (lastIndex > 0) {
                    cleanedResponse = cleanedResponse.substring(0, lastIndex).trim();
                }
                log.debug("마크다운 코드 블록 제거 완료 (Resources)");
            }
            
            // JSON 배열 형식으로 파싱 시도
            if (cleanedResponse.trim().startsWith("[")) {
                JsonNode jsonArray = objectMapper.readTree(cleanedResponse);
                for (JsonNode item : jsonArray) {
                    Map<String, Object> resource = new HashMap<>();
                    resource.put("type", item.has("type") ? item.get("type").asText() : "blog");
                    resource.put("title", item.has("title") ? item.get("title").asText() : "");
                    resource.put("text", item.has("text") ? item.get("text").asText() : "");
                    resource.put("url", item.has("url") && !item.get("url").isNull() ? item.get("url").asText() : null);
                    resource.put("thumbnail", item.has("thumbnail") && !item.get("thumbnail").isNull() ? item.get("thumbnail").asText() : null);
                    resource.put("score", item.has("score") ? item.get("score").asDouble() : 0.8);
                    resourcesList.add(resource);
                }
            } else {
                // 텍스트에서 JSON 객체 추출 시도
                String[] lines = cleanedResponse.split("\n");
                for (String line : lines) {
                    line = line.trim();
                    if (line.startsWith("{") && line.endsWith("}")) {
                        try {
                            JsonNode item = objectMapper.readTree(line);
                            Map<String, Object> resource = new HashMap<>();
                            resource.put("type", item.has("type") ? item.get("type").asText() : "blog");
                            resource.put("title", item.has("title") ? item.get("title").asText() : "");
                            resource.put("text", item.has("text") ? item.get("text").asText() : "");
                            resource.put("url", item.has("url") && !item.get("url").isNull() ? item.get("url").asText() : null);
                            resource.put("thumbnail", item.has("thumbnail") && !item.get("thumbnail").isNull() ? item.get("thumbnail").asText() : null);
                            resource.put("score", item.has("score") ? item.get("score").asDouble() : 0.8);
                            resourcesList.add(resource);
                        } catch (Exception e) {
                            log.warn("JSON 파싱 실패: {}", line, e);
                        }
                    }
                }
            }
        } catch (Exception e) {
            log.error("Resources 응답 파싱 실패", e);
            // 기본값 반환
            Map<String, Object> defaultResource = new HashMap<>();
            defaultResource.put("type", "blog");
            defaultResource.put("title", "관련 자료");
            defaultResource.put("text", response);
            defaultResource.put("url", null);
            defaultResource.put("thumbnail", null);
            defaultResource.put("score", 0.8);
            resourcesList.add(defaultResource);
        }
        return resourcesList;
    }
}


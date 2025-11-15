# 📚 Documents 디렉토리

이 디렉토리에는 **LiveNote AI Gateway**의 상세 문서가 포함되어 있습니다.

---

## 📋 문서 목록

### **전체 시스템**
- [README_en.md](./README_en.md) - 전체 시스템 영문 가이드 (630+ lines)

### **REC (Recommend) 시스템**
- [**REC_전체_가이드.md**](./REC_전체_가이드.md) - ⭐ **REC 시스템 전체 가이드** (아키텍처, 설정 방법, 빠른 시작)
- [REC_OPENALEX_동작과정.md](./REC_OPENALEX_동작과정.md) - OpenAlex 논문 추천 상세 가이드
- [REC_YOUTUBE_동작과정.md](./REC_YOUTUBE_동작과정.md) - YouTube 영상 추천 상세 가이드
- [REC_GOOGLE_동작과정.md](./REC_GOOGLE_동작과정.md) - Google 검색 추천 상세 가이드
- [REC_WIKI_동작과정.md](./REC_WIKI_동작과정.md) - Wikipedia 문서 추천 상세 가이드

### **QA/RAG 시스템**
- [QA_GENERATE_동작과정.md](./QA_GENERATE_동작과정.md) - QA 생성 동작 과정 (8단계)
- [RAG_TEXT_UPSERT_동작과정.md](./RAG_TEXT_UPSERT_동작과정.md) - RAG Text Upsert 동작 과정 (11단계)

---

## 🚀 빠른 시작

### **REC 시스템 사용법**
1. [REC_전체_가이드.md](./REC_전체_가이드.md) 읽기
2. `.env` 파일 설정 (API 키)
3. `server/config.py` 설정 (Provider별)
4. 서버 실행: `uvicorn server.main:app --reload`
5. API 호출: `POST /rec/recommend`

### **각 Provider별 상세 동작 과정**
- OpenAlex가 궁금하다면? → [REC_OPENALEX_동작과정.md](./REC_OPENALEX_동작과정.md)
- YouTube가 궁금하다면? → [REC_YOUTUBE_동작과정.md](./REC_YOUTUBE_동작과정.md)
- Google이 궁금하다면? → [REC_GOOGLE_동작과정.md](./REC_GOOGLE_동작과정.md)
- Wikipedia가 궁금하다면? → [REC_WIKI_동작과정.md](./REC_WIKI_동작과정.md)

---

## 📖 문서 구조

```
documents/
├── README.md                        # 이 파일
├── README_en.md                     # 전체 시스템 영문 가이드
│
├── REC_전체_가이드.md                # ⭐ REC 시스템 메인 가이드
│   ├── 전체 아키텍처
│   ├── 설정 방법 (간단)
│   ├── Provider 비교
│   ├── 공통 동작 흐름
│   └── 빠른 시작
│
├── REC_OPENALEX_동작과정.md         # OpenAlex 상세 가이드
│   ├── 6단계 흐름도
│   ├── 단계별 상세 설명
│   ├── 유효한 설정 가이드
│   ├── 검색 결과 없음 FAQ
│   └── 실제 예시
│
├── REC_YOUTUBE_동작과정.md          # YouTube 상세 가이드
├── REC_GOOGLE_동작과정.md           # Google 상세 가이드
├── REC_WIKI_동작과정.md             # Wikipedia 상세 가이드
│
├── QA_GENERATE_동작과정.md          # QA 생성 가이드
└── RAG_TEXT_UPSERT_동작과정.md      # RAG Upsert 가이드
```

---

## 🔧 문제 해결

### **검색 결과가 없어요**
→ [REC_전체_가이드.md의 문제 해결](./REC_전체_가이드.md#-문제-해결) 참고

### **OpenAlex 검색이 안 돼요**
→ [REC_OPENALEX_동작과정.md의 FAQ](./REC_OPENALEX_동작과정.md#-검색-결과-없음-faq) 참고

### **JSON 파싱 오류**
→ [REC_OPENALEX_동작과정.md의 에러 처리](./REC_OPENALEX_동작과정.md#5-1-llm-병렬-검증-verifytrue) 참고

---

**작성일:** 2025년 11월 14일  
**버전:** 1.0

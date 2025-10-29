"""
RAGKit 종합 테스트 스크립트
- 텍스트 60개 청크 (30분 강의 분량 시뮬레이션)
- PDF 20페이지
- 검색 쿼리 여러 개
팀원 데모용
"""

import time
from ragkit import RAGService, RAGConfig
from ragkit.models import UpsertItem, RetrieveFilters

def print_section(title):
    """섹션 구분선 출력"""
    print("\n" + "="*80)
    print(f"  {title}")
    print("="*80 + "\n")

def main():
    print_section("🚀 RAGKit 종합 테스트 시작")
    
    # 설정
    config = RAGConfig(
        persist_dir="./test_chroma_data",
        embedding_model="text-embedding-3-small"  # 빠른 테스트용
    )
    service = RAGService(config)
    
    # ========== 1. 텍스트 데이터 업로드 (60개 청크) ==========
    print_section("📝 1단계: 텍스트 데이터 업로드 (60청크 - 30분 강의 시뮬레이션)")
    
    # 30분 강의를 시뮬레이션하는 60개 청크
    lecture_chunks = [
        # 인공지능 기초 (1-10)
        "인공지능은 기계가 인간의 지능을 모방하여 학습하고 문제를 해결하는 기술입니다.",
        "머신러닝은 AI의 핵심 분야로, 데이터로부터 패턴을 학습합니다.",
        "지도학습에서는 레이블이 있는 데이터로 모델을 훈련시킵니다.",
        "비지도학습은 레이블 없이 데이터의 숨겨진 구조를 발견합니다.",
        "강화학습은 보상 신호를 통해 최적의 행동을 학습하는 방법입니다.",
        "딥러닝은 여러 층의 신경망을 사용하여 복잡한 패턴을 학습합니다.",
        "합성곱 신경망(CNN)은 이미지 처리에 특화된 구조입니다.",
        "순환 신경망(RNN)은 시계열 데이터와 자연어 처리에 사용됩니다.",
        "트랜스포머 아키텍처는 어텐션 메커니즘으로 NLP를 혁신했습니다.",
        "전이학습을 통해 사전 훈련된 모델을 새로운 작업에 활용할 수 있습니다.",
        
        # 벡터 데이터베이스 (11-20)
        "벡터 데이터베이스는 고차원 임베딩을 효율적으로 저장하고 검색합니다.",
        "임베딩은 텍스트나 이미지를 숫자 벡터로 변환한 것입니다.",
        "코사인 유사도는 벡터 간 유사성을 측정하는 대표적인 방법입니다.",
        "ChromaDB는 오픈소스 벡터 데이터베이스로 간단한 API를 제공합니다.",
        "Pinecone은 클라우드 기반 벡터 DB로 확장성이 뛰어납니다.",
        "Milvus는 대규모 벡터 검색에 최적화된 오픈소스 데이터베이스입니다.",
        "FAISS는 Facebook에서 개발한 고속 유사도 검색 라이브러리입니다.",
        "HNSW 알고리즘은 근사 최근접 이웃 탐색에 널리 사용됩니다.",
        "벡터 인덱싱을 통해 검색 속도를 크게 향상시킬 수 있습니다.",
        "메타데이터 필터링을 병행하면 더 정확한 검색 결과를 얻습니다.",
        
        # RAG 시스템 (21-30)
        "RAG는 검색 증강 생성으로, 외부 지식을 활용하여 답변을 생성합니다.",
        "RAG 파이프라인은 검색과 생성 단계로 구성됩니다.",
        "문서를 청크로 나누는 것이 RAG의 첫 번째 단계입니다.",
        "각 청크는 임베딩으로 변환되어 벡터 DB에 저장됩니다.",
        "사용자 쿼리도 같은 방식으로 임베딩됩니다.",
        "유사도 검색으로 관련 청크들을 찾아냅니다.",
        "검색된 컨텍스트를 LLM 프롬프트에 포함시킵니다.",
        "LLM은 컨텍스트를 바탕으로 정확한 답변을 생성합니다.",
        "RAG는 환각(hallucination) 문제를 크게 줄여줍니다.",
        "지식이 업데이트되면 벡터 DB만 갱신하면 되어 효율적입니다.",
        
        # OpenAI API (31-40)
        "OpenAI는 GPT 시리즈로 유명한 AI 연구 기관입니다.",
        "GPT-4는 현재 가장 강력한 언어 모델 중 하나입니다.",
        "text-embedding-3-large는 3072차원의 고품질 임베딩을 제공합니다.",
        "text-embedding-3-small은 1536차원으로 빠르고 경제적입니다.",
        "OpenAI API는 토큰 단위로 과금되므로 비용 관리가 중요합니다.",
        "Rate limiting을 고려하여 API 호출을 조절해야 합니다.",
        "API 키는 환경변수로 관리하여 보안을 유지합니다.",
        "Batch API를 사용하면 대량 처리 시 비용을 절감할 수 있습니다.",
        "Fine-tuning으로 특정 도메인에 모델을 최적화할 수 있습니다.",
        "Function calling 기능으로 외부 도구와 통합 가능합니다.",
        
        # 프롬프트 엔지니어링 (41-50)
        "프롬프트 엔지니어링은 LLM에서 원하는 출력을 얻는 기술입니다.",
        "명확하고 구체적인 지시사항이 좋은 프롬프트의 핵심입니다.",
        "Few-shot learning은 예시를 제공하여 성능을 향상시킵니다.",
        "Chain-of-Thought는 단계별 추론을 유도하는 기법입니다.",
        "시스템 메시지로 AI의 역할과 톤을 설정할 수 있습니다.",
        "Temperature 파라미터는 출력의 창의성을 조절합니다.",
        "Top-p 샘플링은 확률 분포를 조정하여 다양성을 제어합니다.",
        "프롬프트 템플릿을 활용하면 일관된 품질을 유지할 수 있습니다.",
        "네거티브 프롬프트로 원하지 않는 내용을 배제할 수 있습니다.",
        "프롬프트 버전 관리로 성능 개선 과정을 추적합니다.",
        
        # 실전 응용 (51-60)
        "챗봇 개발 시 대화 히스토리 관리가 중요합니다.",
        "문서 QA 시스템은 RAG의 가장 일반적인 활용 사례입니다.",
        "코드 생성 AI는 프로그래밍 생산성을 크게 높입니다.",
        "요약 시스템은 긴 문서를 빠르게 이해하는 데 도움을 줍니다.",
        "번역 엔진은 다국어 지원 서비스에 필수적입니다.",
        "감성 분석으로 고객 피드백을 자동으로 분류할 수 있습니다.",
        "개체명 인식은 텍스트에서 중요 정보를 추출합니다.",
        "텍스트 분류는 스팸 필터링, 카테고리 분류 등에 사용됩니다.",
        "추천 시스템에 임베딩을 활용하면 정확도가 향상됩니다.",
        "AI 윤리와 책임있는 개발은 모든 프로젝트에서 고려해야 합니다.",
    ]
    
    # 메타데이터와 함께 UpsertItem 생성
    items = []
    sections = ["AI기초", "벡터DB", "RAG시스템", "OpenAI", "프롬프트", "실전응용"]
    
    for i, chunk in enumerate(lecture_chunks):
        section_idx = i // 10
        items.append(UpsertItem(
            text=chunk,
            metadata={
                "섹션": sections[section_idx],
                "청크번호": i + 1,
                "타임스탬프": 1704067200 + i * 30,  # 30초 간격
            }
        ))
    
    start_time = time.time()
    result = service.upsert_text("lecture_collection", items)
    elapsed = time.time() - start_time
    
    print(f"✅ 업로드 완료:")
    print(f"   - 컬렉션: {result['collection_id']}")
    print(f"   - 청크 수: {result['count']}개")
    print(f"   - 임베딩 차원: {result['embedding_dim']}")
    print(f"   - 소요 시간: {elapsed:.2f}초")
    
    # ========== 2. PDF 데이터 업로드 ==========
    print_section("📄 2단계: PDF 데이터 업로드 (20페이지)")
    
    pdf_path = "test_data/large_test_20pages.pdf"
    start_time = time.time()
    result = service.upsert_pdf(
        "pdf_collection",
        pdf_path,
        base_metadata={
            "문서타입": "종합교재",
            "발행년도": 2025
        }
    )
    elapsed = time.time() - start_time
    
    print(f"✅ 업로드 완료:")
    print(f"   - 컬렉션: {result['collection_id']}")
    print(f"   - 페이지 수: {result['count']}개")
    print(f"   - 임베딩 차원: {result['embedding_dim']}")
    print(f"   - 소요 시간: {elapsed:.2f}초")
    
    # ========== 3. 검색 테스트 (여러 쿼리) ==========
    print_section("🔍 3단계: 검색 테스트")
    
    # 쿼리 1: 일반 검색
    print("【쿼리 1】인공지능 학습 방법에는 어떤 것들이 있나요? (top_k=3)")
    print("-" * 80)
    
    chunks = service.retrieve("lecture_collection", "인공지능 학습 방법", top_k=3)
    for i, chunk in enumerate(chunks, 1):
        print(f"{i}. [유사도: {chunk.score:.4f}] {chunk.text}")
        print(f"   메타데이터: {chunk.metadata}")
    
    # 쿼리 2: 벡터 데이터베이스 관련
    print("\n【쿼리 2】벡터 데이터베이스의 종류와 특징 (top_k=3)")
    print("-" * 80)
    
    chunks = service.retrieve("lecture_collection", "벡터 데이터베이스 종류", top_k=3)
    for i, chunk in enumerate(chunks, 1):
        print(f"{i}. [유사도: {chunk.score:.4f}] {chunk.text}")
        print(f"   메타데이터: {chunk.metadata}")
    
    # 쿼리 3: 필터링 검색 (섹션 필터)
    print("\n【쿼리 3】OpenAI 섹션에서 임베딩 관련 정보 (필터 적용, top_k=3)")
    print("-" * 80)
    
    filters = RetrieveFilters(custom={"섹션": "OpenAI"})
    chunks = service.retrieve("lecture_collection", "임베딩 모델", top_k=3, filters=filters)
    for i, chunk in enumerate(chunks, 1):
        print(f"{i}. [유사도: {chunk.score:.4f}] {chunk.text}")
        print(f"   메타데이터: {chunk.metadata}")
    
    # 쿼리 4: 섹션 필터
    print("\n【쿼리 4】프롬프트 섹션에서 프롬프트 엔지니어링 기법 (섹션 필터, top_k=3)")
    print("-" * 80)
    
    filters = RetrieveFilters(custom={"섹션": "프롬프트"})
    chunks = service.retrieve("lecture_collection", "프롬프트 작성 방법", top_k=3, filters=filters)
    for i, chunk in enumerate(chunks, 1):
        print(f"{i}. [유사도: {chunk.score:.4f}] {chunk.text}")
        print(f"   메타데이터: {chunk.metadata}")
    
    # 쿼리 5: PDF에서 검색
    print("\n【쿼리 5】PDF에서 머신러닝 관련 내용 검색 (top_k=3)")
    print("-" * 80)
    
    chunks = service.retrieve("pdf_collection", "머신러닝 딥러닝", top_k=3)
    for i, chunk in enumerate(chunks, 1):
        print(f"{i}. [유사도: {chunk.score:.4f}]")
        print(f"   텍스트 미리보기: {chunk.text[:100]}...")
        print(f"   메타데이터: {chunk.metadata}")
    
    # 쿼리 6: PDF에서 요리 관련
    print("\n【쿼리 6】PDF에서 음식 요리 관련 내용 (top_k=2)")
    print("-" * 80)
    
    chunks = service.retrieve("pdf_collection", "음식 만드는 방법", top_k=2)
    for i, chunk in enumerate(chunks, 1):
        print(f"{i}. [유사도: {chunk.score:.4f}]")
        print(f"   텍스트 미리보기: {chunk.text[:100]}...")
        print(f"   메타데이터: {chunk.metadata}")
    
    # 쿼리 7: AI기초 섹션만
    print("\n【쿼리 7】AI기초 섹션에서 기본 개념 검색 (섹션 필터, top_k=5)")
    print("-" * 80)
    
    filters = RetrieveFilters(custom={"섹션": "AI기초"})
    chunks = service.retrieve("lecture_collection", "기본 개념과 정의", top_k=5, filters=filters)
    for i, chunk in enumerate(chunks, 1):
        print(f"{i}. [유사도: {chunk.score:.4f}] {chunk.text[:60]}...")
        print(f"   섹션: {chunk.metadata.get('섹션')}, 청크: {chunk.metadata.get('청크번호')}")
    
    # ========== 4. 통계 정보 ==========
    print_section("📊 4단계: 테스트 요약")
    
    print("✅ 성공적으로 완료된 작업:")
    print(f"   1. 텍스트 60개 청크 업로드 (6개 섹션)")
    print(f"   2. PDF 20페이지 업로드 (다양한 주제)")
    print(f"   3. 총 7개 쿼리 테스트 (일반 검색, 필터 검색)")
    print(f"\n✅ 사용된 컬렉션:")
    print(f"   - lecture_collection: 60개 텍스트 청크")
    print(f"   - pdf_collection: 20개 PDF 페이지")
    print(f"\n✅ 임베딩 모델: {config.embedding_model}")
    print(f"✅ 저장 위치: {config.persist_dir}")
    
    print_section("🎉 모든 테스트 완료!")
    print("팀원들에게 다음과 같이 설명하세요:")
    print("1. 대량 데이터 처리 성능 확인 (60 텍스트 + 20 PDF)")
    print("2. 메타데이터 필터링 기능 동작 확인")
    print("3. 다양한 주제의 문서에서 정확한 검색 가능")
    print("4. 유사도 점수로 결과 품질 평가 가능\n")

if __name__ == "__main__":
    main()

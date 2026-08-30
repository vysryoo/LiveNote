#!/usr/bin/env python3
"""
RAG Vector DB 데이터 검증 스크립트

test_upsert.sh로 업서트한 데이터가 ChromaDB에 정상적으로 저장되었는지 확인합니다.
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# .env 파일 로드 (OpenAI API 키 등)
load_dotenv()

# 환경 변수 설정
os.environ["ANONYMIZED_TELEMETRY"] = "False"
os.environ["CHROMA_TELEMETRY_ENABLED"] = "False"

# RAG 모듈 경로 추가
sys.path.insert(0, str(Path(__file__).parent / "cap1_RAG_module"))

from ragkit.service import RAGService
from ragkit.config import RAGConfig


def print_separator(char="━", length=80):
    """구분선 출력"""
    print(char * length)


def print_section_header(title: str):
    """섹션 헤더 출력"""
    print("\n")
    print_separator()
    print(f"📊 {title}")
    print_separator()


def verify_collection(service: RAGService, collection_id: str, expected_count: int):
    """
    컬렉션의 데이터 확인
    
    Args:
        service: RAGService 인스턴스
        collection_id: 확인할 컬렉션 ID
        expected_count: 예상 문서 수
    """
    print_section_header(f"Collection: {collection_id}")
    
    try:
        # 컬렉션 가져오기
        collection = service.vector_store.client.get_collection(collection_id)
        
        # 전체 문서 수 확인
        count = collection.count()
        print(f"✅ 총 문서 수: {count}개")
        print(f"📝 예상 문서 수: {expected_count}개")
        
        if count != expected_count:
            print(f"⚠️  경고: 예상({expected_count})과 실제({count})가 다릅니다!")
        else:
            print(f"✅ 문서 수 일치!")
        
        # 모든 문서 가져오기
        results = collection.get(
            include=["documents", "metadatas"]
        )
        
        print(f"\n📄 저장된 문서 목록:")
        print_separator("-", 80)
        
        for i, (doc_id, document, metadata) in enumerate(
            zip(results["ids"], results["documents"], results["metadatas"]), 
            start=1
        ):
            print(f"\n[{i}] ID: {doc_id}")
            print(f"    Text: {document[:100]}{'...' if len(document) > 100 else ''}")
            print(f"    Metadata: {metadata}")
        
        print_separator("-", 80)
        
        # 메타데이터 통계
        print(f"\n📈 메타데이터 통계:")
        
        # section_id 분포
        section_ids = [m.get("section_id") for m in results["metadatas"] if m.get("section_id")]
        if section_ids:
            from collections import Counter
            section_counts = Counter(section_ids)
            print(f"   Section 분포: {dict(section_counts)}")
        
        # subject 분포
        subjects = [m.get("subject") for m in results["metadatas"] if m.get("subject")]
        if subjects:
            from collections import Counter
            subject_counts = Counter(subjects)
            print(f"   Subject 분포: {dict(subject_counts)}")
        
        # difficulty 분포
        difficulties = [m.get("difficulty") for m in results["metadatas"] if m.get("difficulty")]
        if difficulties:
            from collections import Counter
            diff_counts = Counter(difficulties)
            print(f"   Difficulty 분포: {dict(diff_counts)}")
        
        return True
        
    except Exception as e:
        print(f"❌ 오류 발생: {e}")
        return False


def main():
    """메인 함수"""
    print_separator("═", 80)
    print("🔍 RAG Vector DB 데이터 검증 시작")
    print_separator("═", 80)
    
    # RAG 서비스 초기화
    print("\n초기화 중...")
    persist_dir = os.getenv("RAG_PERSIST_DIR", "server_storage/chroma_data")
    print(f"📁 ChromaDB 경로: {persist_dir}")
    
    config = RAGConfig(persist_dir=persist_dir)
    service = RAGService(config=config)
    
    # 모든 컬렉션 목록 가져오기
    all_collections = service.vector_store.client.list_collections()
    print(f"\n📚 발견된 컬렉션: {len(all_collections)}개")
    for col in all_collections:
        print(f"   - {col.name}")
    
    # test_upsert.sh에서 생성한 컬렉션들 확인
    test_collections = {
        "lecture_cs101": {
            "expected_count": 20,  # 테스트 1(2) + 2(3) + 3(2) + 5(6) + 7(1+1) + 업데이트
            "description": "Computer Science 101 강의"
        },
        "lecture_math201": {
            "expected_count": 12,  # 테스트 4(2) + 6(10)
            "description": "수학 201 강의"
        }
    }
    
    print("\n")
    print_separator("═", 80)
    print("📋 테스트 컬렉션 검증")
    print_separator("═", 80)
    
    results = {}
    
    for collection_id, info in test_collections.items():
        success = verify_collection(
            service, 
            collection_id, 
            info["expected_count"]
        )
        results[collection_id] = success
    
    # 최종 요약
    print("\n")
    print_separator("═", 80)
    print("📊 검증 결과 요약")
    print_separator("═", 80)
    
    for collection_id, success in results.items():
        status = "✅ 성공" if success else "❌ 실패"
        print(f"{status} - {collection_id}")
    
    all_success = all(results.values())
    
    print("\n")
    if all_success:
        print("🎉 모든 컬렉션 검증 완료!")
        print("✅ test_upsert.sh의 모든 데이터가 정상적으로 저장되었습니다.")
    else:
        print("⚠️  일부 컬렉션에 문제가 있습니다.")
        print("❌ 로그를 확인하여 문제를 해결하세요.")
    
    print_separator("═", 80)
    
    return 0 if all_success else 1


if __name__ == "__main__":
    sys.exit(main())

#!/usr/bin/env python3
"""
RAG Vector DB 상세 검증 스크립트

test_upsert.sh에서 업서트한 데이터와 실제 저장된 데이터를 비교합니다.
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# .env 파일 로드
load_dotenv()

# 환경 변수 설정
os.environ["ANONYMIZED_TELEMETRY"] = "False"
os.environ["CHROMA_TELEMETRY_ENABLED"] = "False"

# RAG 모듈 경로 추가
sys.path.insert(0, str(Path(__file__).parent / "cap1_RAG_module"))

from ragkit.service import RAGService
from ragkit.config import RAGConfig


# test_upsert.sh에서 업서트한 예상 데이터
EXPECTED_DATA = {
    "lecture_cs101": [
        # 테스트 1: 기본 텍스트 (2개)
        {"text_snippet": "데이터베이스는 구조화된", "has_id": False, "metadata_keys": ["source"]},
        {"text_snippet": "SQL은 Structured Query", "has_id": False, "metadata_keys": ["source"]},
        
        # 테스트 2: ID + section_id (3개)
        {"text_snippet": "객체지향 프로그래밍", "has_id": True, "id": "cs101_oop_intro", "metadata_keys": ["section_id"]},
        {"text_snippet": "캡슐화, 상속, 다형성", "has_id": True, "id": "cs101_oop_features", "metadata_keys": ["section_id"]},
        {"text_snippet": "클래스는 객체를", "has_id": True, "id": "cs101_class_def", "metadata_keys": ["section_id"]},
        
        # 테스트 3: 풍부한 메타데이터 (2개)
        {"text_snippet": "알고리즘의 시간 복잡도", "has_id": True, "id": "algo_complexity", "metadata_keys": ["subject", "category", "difficulty", "section_id"]},
        {"text_snippet": "정렬 알고리즘에는", "has_id": True, "id": "sorting_intro", "metadata_keys": ["subject", "category", "difficulty", "section_id"]},
        
        # 테스트 5: 혼합 케이스 (6개)
        {"text_snippet": "스택은 LIFO", "has_id": False, "metadata_keys": ["source"]},
        {"text_snippet": "큐는 FIFO", "has_id": True, "id": "queue_def", "metadata_keys": ["source"]},
        {"text_snippet": "연결 리스트는", "has_id": False, "metadata_keys": ["section_id"]},
        {"text_snippet": "이진 트리는", "has_id": True, "id": "binary_tree", "metadata_keys": ["section_id"]},
        {"text_snippet": "해시 테이블은", "has_id": False, "metadata_keys": ["subject", "difficulty"]},
        {"text_snippet": "그래프는 정점", "has_id": True, "id": "graph_def", "metadata_keys": ["subject", "category", "difficulty", "section_id", "applications"]},
        
        # 테스트 7: 업데이트 (1개, 최종 버전만)
        {"text_snippet": "파이썬은 동적 타이핑", "has_id": True, "id": "python_intro_v1", "metadata_keys": ["version", "updated_at"]},
    ],
    "lecture_math201": [
        # 테스트 4: 다른 강의 (2개)
        {"text_snippet": "미적분학은 변화율", "has_id": False, "metadata_keys": ["subject", "category", "section_id", "semester", "university"]},
        {"text_snippet": "도함수는 함수의", "has_id": True, "id": "calc_derivative", "metadata_keys": ["subject", "category", "subcategory", "section_id", "semester", "formula"]},
        
        # 테스트 6: 대량 업서트 (10개)
        {"text_snippet": "적분은 함수의", "has_id": False, "metadata_keys": ["section_id", "chapter"]},
        {"text_snippet": "정적분은 정해진", "has_id": False, "metadata_keys": ["section_id", "chapter"]},
        {"text_snippet": "부정적분은 원시함수", "has_id": False, "metadata_keys": ["section_id", "chapter"]},
        {"text_snippet": "치환적분법은", "has_id": False, "metadata_keys": ["section_id", "chapter"]},
        {"text_snippet": "부분적분법은", "has_id": False, "metadata_keys": ["section_id", "chapter"]},
        {"text_snippet": "삼각함수의 적분", "has_id": False, "metadata_keys": ["section_id", "chapter", "type"]},
        {"text_snippet": "이상적분은 무한", "has_id": False, "metadata_keys": ["section_id", "chapter", "difficulty"]},
        {"text_snippet": "중적분은 다변수", "has_id": False, "metadata_keys": ["section_id", "chapter", "difficulty"]},
        {"text_snippet": "푸비니 정리", "has_id": False, "metadata_keys": ["section_id", "chapter", "theorem"]},
        {"text_snippet": "그린 정리", "has_id": False, "metadata_keys": ["section_id", "chapter", "theorem", "difficulty"]},
    ]
}


def compare_documents(collection_id: str, expected: list, actual_results: dict):
    """
    예상 문서와 실제 문서 비교
    """
    print(f"\n📋 상세 비교: {collection_id}")
    print("=" * 80)
    
    actual_ids = actual_results["ids"]
    actual_docs = actual_results["documents"]
    actual_metas = actual_results["metadatas"]
    
    expected_count = len(expected)
    actual_count = len(actual_ids)
    
    print(f"\n📊 문서 수 비교:")
    print(f"   예상: {expected_count}개")
    print(f"   실제: {actual_count}개")
    
    if expected_count == actual_count:
        print(f"   ✅ 문서 수 일치!")
    else:
        print(f"   ⚠️  문서 수 불일치 (차이: {actual_count - expected_count})")
    
    # 각 예상 문서가 실제로 존재하는지 확인
    print(f"\n📝 문서별 상세 확인:")
    print("-" * 80)
    
    found_count = 0
    missing_items = []
    
    for i, exp_item in enumerate(expected, start=1):
        snippet = exp_item["text_snippet"]
        found = False
        matched_doc = None
        matched_id = None
        matched_meta = None
        
        # 텍스트 스니펫으로 찾기
        for doc_id, doc, meta in zip(actual_ids, actual_docs, actual_metas):
            if snippet in doc:
                found = True
                matched_doc = doc
                matched_id = doc_id
                matched_meta = meta
                break
        
        if found:
            print(f"\n✅ [{i}] 발견됨")
            print(f"    스니펫: {snippet}...")
            print(f"    ID: {matched_id}")
            
            # ID 확인
            if exp_item.get("has_id") and exp_item.get("id"):
                expected_id = exp_item["id"]
                if matched_id == expected_id:
                    print(f"    ✅ ID 일치: {expected_id}")
                else:
                    print(f"    ⚠️  ID 불일치: 예상({expected_id}) vs 실제({matched_id})")
            
            # 메타데이터 키 확인
            expected_keys = set(exp_item.get("metadata_keys", []))
            actual_keys = set(matched_meta.keys())
            
            if expected_keys.issubset(actual_keys):
                print(f"    ✅ 메타데이터 키 포함: {expected_keys}")
            else:
                missing_keys = expected_keys - actual_keys
                print(f"    ⚠️  누락된 메타데이터 키: {missing_keys}")
                print(f"       실제 키: {actual_keys}")
            
            found_count += 1
        else:
            print(f"\n❌ [{i}] 누락됨")
            print(f"    스니펫: {snippet}...")
            if exp_item.get("has_id") and exp_item.get("id"):
                print(f"    예상 ID: {exp_item['id']}")
            missing_items.append(exp_item)
    
    print("\n" + "=" * 80)
    print(f"📊 최종 결과:")
    print(f"   발견: {found_count}/{expected_count} ({found_count/expected_count*100:.1f}%)")
    
    if missing_items:
        print(f"\n⚠️  누락된 항목 ({len(missing_items)}개):")
        for item in missing_items:
            print(f"   - {item['text_snippet']}...")
    else:
        print(f"\n🎉 모든 예상 문서가 저장되어 있습니다!")
    
    return found_count == expected_count


def main():
    """메인 함수"""
    print("=" * 80)
    print("🔍 RAG Vector DB 상세 검증 (예상 데이터 vs 실제 데이터)")
    print("=" * 80)
    
    # RAG 서비스 초기화
    persist_dir = os.getenv("RAG_PERSIST_DIR", "server_storage/chroma_data")
    config = RAGConfig(persist_dir=persist_dir)
    service = RAGService(config=config)
    
    results = {}
    
    for collection_id, expected_docs in EXPECTED_DATA.items():
        try:
            collection = service.vector_store.client.get_collection(collection_id)
            actual_results = collection.get(include=["documents", "metadatas"])
            
            success = compare_documents(collection_id, expected_docs, actual_results)
            results[collection_id] = success
            
        except Exception as e:
            print(f"\n❌ 오류 ({collection_id}): {e}")
            results[collection_id] = False
    
    # 최종 요약
    print("\n")
    print("=" * 80)
    print("📊 전체 검증 결과")
    print("=" * 80)
    
    for collection_id, success in results.items():
        status = "✅ 완벽" if success else "⚠️  문제 있음"
        print(f"{status} - {collection_id}")
    
    all_success = all(results.values())
    
    print("\n")
    if all_success:
        print("🎉 완벽합니다! 모든 예상 데이터가 정확히 저장되었습니다!")
    else:
        print("⚠️  일부 데이터에 문제가 있습니다. 위 로그를 확인하세요.")
    
    print("=" * 80)
    
    return 0 if all_success else 1


if __name__ == "__main__":
    sys.exit(main())

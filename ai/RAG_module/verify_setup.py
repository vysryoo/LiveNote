#!/usr/bin/env python3
"""RAGKit 설치 및 구조 검증 스크립트."""

import sys
from pathlib import Path


def check_structure():
    """프로젝트 구조 검증."""
    print("🔍 RAGKit 프로젝트 구조 검증\n")
    
    base = Path(__file__).parent
    
    required_files = [
        # Core library
        "ragkit/__init__.py",
        "ragkit/config.py",
        "ragkit/models.py",
        "ragkit/service.py",
        "ragkit/embeddings/__init__.py",
        "ragkit/embeddings/openai.py",
        "ragkit/vectordb/__init__.py",
        "ragkit/vectordb/chroma.py",
        "ragkit/utils/__init__.py",
        "ragkit/utils/pdf.py",
        "ragkit/utils/text.py",
        
        # Tests
        "tests/conftest.py",
        "tests/test_upsert_text.py",
        "tests/test_upsert_pdf.py",
        "tests/test_retrieve.py",
        
        # Examples
        "examples/test_light.py",
        "examples/ingest_pdf_pages.py",
        
        # Test data
        "test_data/simple_test.pdf",
        "test_data/sample_lecture.pdf",
        
        # Documentation
        "README.md",
        "USAGE_GUIDE.md",
        "requirements.txt",
        "pyproject.toml",
    ]
    
    missing = []
    found = []
    
    for file_path in required_files:
        full_path = base / file_path
        if full_path.exists():
            found.append(file_path)
            print(f"  ✅ {file_path}")
        else:
            missing.append(file_path)
            print(f"  ❌ {file_path}")
    
    print(f"\n📊 검증 결과: {len(found)}/{len(required_files)} 파일 존재")
    
    if missing:
        print(f"\n⚠️  누락된 파일: {len(missing)}개")
        for f in missing:
            print(f"    - {f}")
        return False
    
    return True


def check_imports():
    """주요 모듈 import 검증."""
    print("\n🔍 모듈 Import 검증\n")
    
    try:
        from ragkit import RAGService, RAGConfig
        print("  ✅ RAGService, RAGConfig")
    except ImportError as e:
        print(f"  ❌ RAGService, RAGConfig: {e}")
        return False
    
    try:
        from ragkit.models import UpsertItem, RetrieveFilters, RetrievedChunk
        print("  ✅ UpsertItem, RetrieveFilters, RetrievedChunk")
    except ImportError as e:
        print(f"  ❌ Models: {e}")
        return False
    
    try:
        from ragkit.embeddings.openai import OpenAIEmbeddingService
        print("  ✅ OpenAIEmbeddingService")
    except ImportError as e:
        print(f"  ❌ OpenAIEmbeddingService: {e}")
        return False
    
    try:
        from ragkit.vectordb.chroma import ChromaVectorStore
        print("  ✅ ChromaVectorStore")
    except ImportError as e:
        print(f"  ❌ ChromaVectorStore: {e}")
        return False
    
    try:
        from ragkit.utils.pdf import load_pdf_pages
        from ragkit.utils.text import normalize_text, make_id
        print("  ✅ Utility functions")
    except ImportError as e:
        print(f"  ❌ Utilities: {e}")
        return False
    
    return True


def check_dependencies():
    """필수 패키지 설치 확인."""
    print("\n🔍 필수 패키지 확인\n")
    
    packages = {
        "openai": "OpenAI Python SDK",
        "chromadb": "Chroma vector database",
        "pypdf": "PDF processing",
        "pytest": "Testing framework",
    }
    
    all_installed = True
    
    for package, description in packages.items():
        try:
            __import__(package)
            print(f"  ✅ {package:15s} - {description}")
        except ImportError:
            print(f"  ❌ {package:15s} - {description} (NOT INSTALLED)")
            all_installed = False
    
    return all_installed


def print_summary():
    """사용 가이드 요약."""
    print("\n" + "="*70)
    print("✨ RAGKit 라이브러리가 준비되었습니다!")
    print("="*70)
    
    print("\n📚 다음 단계:")
    print("  1. OpenAI API 키 설정:")
    print("     export OPENAI_API_KEY='your-key-here'")
    print()
    print("  2. 간단한 예제 실행:")
    print("     python examples/test_light.py")
    print()
    print("  3. PDF 수집 예제:")
    print("     python examples/ingest_pdf_pages.py test_data/sample_lecture.pdf my_collection")
    print()
    print("  4. 테스트 실행:")
    print("     pytest -v -s")
    print()
    print("  5. 상세 문서:")
    print("     - README.md: 전체 문서")
    print("     - USAGE_GUIDE.md: 사용 가이드")
    print()
    print("="*70)


def main():
    """메인 검증 함수."""
    print("\n" + "="*70)
    print("🚀 RAGKit 프로젝트 검증 스크립트")
    print("="*70 + "\n")
    
    # 1. 구조 검증
    structure_ok = check_structure()
    
    # 2. Import 검증
    imports_ok = check_imports()
    
    # 3. 패키지 검증
    deps_ok = check_dependencies()
    
    # 결과
    print("\n" + "="*70)
    if structure_ok and imports_ok and deps_ok:
        print("✅ 모든 검증 통과!")
        print_summary()
        return 0
    else:
        print("❌ 일부 검증 실패")
        print("\n필요한 조치:")
        if not deps_ok:
            print("  - 패키지 설치: pip install openai chromadb pypdf pytest")
        if not imports_ok:
            print("  - 가상환경 확인: source .venv/bin/activate")
        return 1


if __name__ == "__main__":
    sys.exit(main())

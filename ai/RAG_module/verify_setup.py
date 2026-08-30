#!/usr/bin/env python3
"""
RAGKit 설치 확인 스크립트
모든 필수 패키지와 환경 설정이 올바른지 검증합니다.
"""

import sys
import os

def print_header(text):
    """헤더 출력"""
    print("\n" + "="*70)
    print(f"  {text}")
    print("="*70)

def print_success(text):
    """성공 메시지"""
    print(f"✅ {text}")

def print_error(text):
    """에러 메시지"""
    print(f"❌ {text}")

def print_warning(text):
    """경고 메시지"""
    print(f"⚠️  {text}")

def check_python_version():
    """Python 버전 확인"""
    print("\n[1/6] Python 버전 확인...")
    version = sys.version_info
    if version.major == 3 and version.minor >= 11:
        print_success(f"Python {version.major}.{version.minor}.{version.micro}")
        return True
    else:
        print_error(f"Python 3.11+ 필요 (현재: {version.major}.{version.minor}.{version.micro})")
        return False

def check_imports():
    """필수 패키지 import 확인"""
    print("\n[2/6] 필수 패키지 확인...")
    packages = {
        'chromadb': 'ChromaDB (벡터 데이터베이스)',
        'openai': 'OpenAI (임베딩 생성)',
        'pypdf': 'PyPDF (PDF 파싱)',
        'dotenv': 'python-dotenv (.env 로더)',
        'reportlab': 'ReportLab (PDF 생성)',
        'ragkit': 'RAGKit (메인 패키지)'
    }
    
    all_ok = True
    for package, description in packages.items():
        try:
            if package == 'dotenv':
                __import__('dotenv')
            else:
                __import__(package)
            print_success(f"{description}")
        except ImportError:
            print_error(f"{description} - 설치 필요")
            all_ok = False
    
    return all_ok

def check_ragkit_modules():
    """RAGKit 모듈 확인"""
    print("\n[3/6] RAGKit 모듈 확인...")
    try:
        from ragkit import RAGService, RAGConfig
        from ragkit.models import UpsertItem, RetrieveFilters
        from ragkit.embeddings import OpenAIEmbeddingService
        from ragkit.vectordb import ChromaVectorStore
        print_success("RAGService")
        print_success("RAGConfig")
        print_success("UpsertItem, RetrieveFilters")
        print_success("OpenAIEmbeddingService")
        print_success("ChromaVectorStore")
        return True
    except ImportError as e:
        print_error(f"RAGKit 모듈 import 실패: {e}")
        return False

def check_env_file():
    """환경 변수 파일 확인"""
    print("\n[4/6] 환경 변수 확인...")
    
    if not os.path.exists('.env'):
        print_error(".env 파일 없음")
        print("  해결: echo 'OPENAI_API_KEY=sk-...' > .env")
        return False
    
    print_success(".env 파일 존재")
    
    # .env 파일 읽기
    from dotenv import load_dotenv
    load_dotenv()
    
    api_key = os.getenv('OPENAI_API_KEY')
    if not api_key:
        print_error("OPENAI_API_KEY 환경 변수 없음")
        return False
    
    if not api_key.startswith('sk-'):
        print_warning("API 키 형식이 이상함 (sk-로 시작해야 함)")
        return False
    
    print_success(f"OPENAI_API_KEY 설정됨 ({api_key[:15]}...)")
    return True

def check_test_data():
    """테스트 데이터 확인"""
    print("\n[5/6] 테스트 데이터 확인...")
    
    test_files = {
        'test_data/': '테스트 데이터 디렉토리',
        'create_large_test_pdf.py': 'PDF 생성 스크립트',
        'all_test.py': '종합 테스트 스크립트'
    }
    
    all_ok = True
    for file, description in test_files.items():
        if os.path.exists(file):
            print_success(description)
        else:
            print_warning(f"{description} 없음")
            all_ok = False
    
    # PDF 파일 확인 (선택)
    if os.path.exists('test_data/large_test_20pages.pdf'):
        print_success("20페이지 테스트 PDF")
    else:
        print_warning("20페이지 테스트 PDF 없음 (create_large_test_pdf.py 실행 필요)")
    
    return all_ok

def check_basic_functionality():
    """기본 기능 테스트"""
    print("\n[6/6] 기본 기능 테스트...")
    
    try:
        from ragkit import RAGConfig
        from dotenv import load_dotenv
        load_dotenv()
        
        # Config 생성
        config = RAGConfig(
            persist_dir="./test_verify_chroma",
            embedding_model="text-embedding-3-small"
        )
        print_success("RAGConfig 생성")
        
        # Service 생성 (API 키 필요)
        from ragkit import RAGService
        service = RAGService(config)
        print_success("RAGService 초기화")
        
        # 임시 디렉토리 삭제
        import shutil
        if os.path.exists("./test_verify_chroma"):
            shutil.rmtree("./test_verify_chroma")
        
        return True
    except Exception as e:
        print_error(f"기능 테스트 실패: {e}")
        return False

def main():
    """메인 함수"""
    print_header("🔍 RAGKit 설치 확인")
    
    results = []
    results.append(check_python_version())
    results.append(check_imports())
    results.append(check_ragkit_modules())
    results.append(check_env_file())
    results.append(check_test_data())
    results.append(check_basic_functionality())
    
    # 결과 요약
    print_header("📊 검증 결과")
    
    passed = sum(results)
    total = len(results)
    
    print(f"\n통과: {passed}/{total}")
    
    if all(results):
        print_success("모든 검증 통과! 🎉")
        print("\n다음 단계:")
        print("  1. 종합 테스트: python all_test.py")
        print("  2. 단위 테스트: pytest -v")
        print("  3. 문서 확인: cat README_KR.md")
        return 0
    else:
        print_error("일부 검증 실패")
        print("\n해결 방법:")
        print("  1. setup.sh 재실행")
        print("  2. pip install -e . 재설치")
        print("  3. .env 파일 확인")
        return 1

if __name__ == "__main__":
    sys.exit(main())

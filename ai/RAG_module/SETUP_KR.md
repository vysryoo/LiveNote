# RAGKit 설치 및 설정 가이드

이 가이드는 RAGKit을 처음부터 설치하고 종합 테스트까지 실행하는 완전한 절차를 안내합니다.

## 📋 목차

1. [사전 요구사항](#1-사전-요구사항)
2. [환경 설정](#2-환경-설정)
3. [패키지 설치](#3-패키지-설치)
4. [API 키 설정](#4-api-키-설정)
5. [설치 확인](#5-설치-확인)
6. [종합 테스트 실행](#6-종합-테스트-실행)
7. [자동 설치 스크립트](#7-자동-설치-스크립트)

---

## 1. 사전 요구사항

### 필수 소프트웨어

- **Python 3.11 이상**
  ```bash
  python --version
  # 출력 예: Python 3.11.5
  ```

- **pip** (Python 패키지 매니저)
  ```bash
  pip --version
  # 출력 예: pip 23.2.1
  ```

- **OpenAI API 키**
  - [OpenAI 플랫폼](https://platform.openai.com/api-keys)에서 발급
  - 형식: `sk-...` (51자)

### 권장 사항

- **가상 환경 사용** (venv, conda 등)
- **Git** (버전 관리용)

---

## 2. 환경 설정

### 방법 1: venv 사용 (권장)

```bash
# 1. 프로젝트 디렉토리로 이동
cd RAG_module

# 2. 가상 환경 생성
python -m venv .venv

# 3. 가상 환경 활성화
# macOS/Linux:
source .venv/bin/activate

# Windows:
.venv\Scripts\activate

# 4. 확인 (프롬프트에 (.venv) 표시됨)
which python
# 출력: /path/to/RAG_module/.venv/bin/python
```

### 방법 2: conda 사용

```bash
# 1. conda 환경 생성
conda create -n ragkit python=3.11 -y

# 2. 환경 활성화
conda activate ragkit

# 3. 확인
which python
# 출력: /path/to/anaconda3/envs/ragkit/bin/python
```

---

## 3. 패키지 설치

### 자동 설치 (editable 모드)

```bash
# 가상 환경 활성화 상태에서
pip install -e .
```

**이 명령어가 자동으로 설치하는 것:**
- ✅ chromadb (벡터 데이터베이스)
- ✅ openai (OpenAI API 클라이언트)
- ✅ python-dotenv (환경 변수 관리)
- ✅ pypdf (PDF 처리)
- ✅ pytest (테스트 프레임워크)
- ✅ 기타 의존성 (numpy, pydantic 등)

### 수동 설치 (필요시)

```bash
# requirements.txt 사용
pip install -r requirements.txt

# 개별 패키지 설치
pip install chromadb>=0.5.10
pip install openai>=1.30
pip install python-dotenv>=1.0
pip install pypdf>=4.2
```

### 설치 확인

```bash
# 설치된 패키지 확인
pip list | grep -E "chromadb|openai|pypdf"

# 출력 예:
# chromadb     0.5.23
# openai       1.109.1
# pypdf        4.3.1
```

---

## 4. API 키 설정

### 방법 1: .env 파일 (권장)

```bash
# 1. .env 파일 생성
cat > .env << EOF
OPENAI_API_KEY=sk-your-actual-api-key-here
EOF

# 2. 파일 확인
cat .env
# 출력: OPENAI_API_KEY=sk-...

# 3. 권한 설정 (보안)
chmod 600 .env
```

### 방법 2: 환경 변수

```bash
# 현재 세션에만 적용
export OPENAI_API_KEY='sk-your-actual-api-key-here'

# 영구 적용 (bashrc/zshrc)
echo 'export OPENAI_API_KEY="sk-your-actual-api-key-here"' >> ~/.bashrc
source ~/.bashrc
```

### API 키 확인

```bash
# 환경 변수 확인
echo $OPENAI_API_KEY
# 출력: sk-...

# Python에서 확인
python -c "import os; print('✅ API 키 설정됨' if os.getenv('OPENAI_API_KEY') else '❌ API 키 없음')"
```

---

## 5. 설치 확인

### 간단한 테스트

```bash
# ragkit 임포트 테스트
python -c "from ragkit import RAGService; print('✅ RAGKit 설치 성공!')"
```

### verify_setup.py 실행

```bash
python verify_setup.py
```

**기대 출력:**
```
✅ Python version: 3.11.5
✅ ragkit package installed
✅ chromadb installed
✅ openai installed
✅ OPENAI_API_KEY configured
✅ All checks passed!
```

---

## 6. 종합 테스트 실행

### 테스트 데이터 생성 (선택사항)

```bash
# 20페이지 테스트 PDF 생성 (이미 있으면 생략 가능)
python create_large_test_pdf.py
```

**출력:**
```
✅ PDF 생성 완료: test_data/large_test_20pages.pdf
   - 페이지 수: 20
   - 주제: 20개 (ML, 요리, 블록체인 등)
```

### 종합 테스트 실행

```bash
# 방법 1: 직접 실행
source .venv/bin/activate
python all_test.py
```

**기대 출력:**
```
================================================================================
  🚀 RAGKit 종합 테스트 시작
================================================================================

================================================================================
  📝 1단계: 텍스트 데이터 업로드 (60청크 - 30분 강의 시뮬레이션)
================================================================================

✅ 업로드 완료:
   - 컬렉션: lecture_collection
   - 청크 수: 60개
   - 임베딩 차원: 1536
   - 소요 시간: 1.16초

================================================================================
  📄 2단계: PDF 데이터 업로드 (20페이지)
================================================================================

✅ 업로드 완료:
   - 컬렉션: pdf_collection
   - 페이지 수: 20개
   - 임베딩 차원: 1536
   - 소요 시간: 1.27초

...

🎉 모든 테스트 완료!
```

### pytest 실행 (단위 테스트)

```bash
# 모든 테스트 실행
pytest -v

# 특정 테스트만
pytest tests/test_upsert_text.py -v
pytest tests/test_retrieve.py -v
```

---

## 7. 자동 설치 스크립트

### setup.sh 사용 (macOS/Linux)

```bash
# 실행 권한 부여
chmod +x setup.sh

# 스크립트 실행
./setup.sh
```

**스크립트가 자동으로 수행:**
1. ✅ Python 버전 확인
2. ✅ 가상 환경 생성/활성화
3. ✅ 패키지 설치
4. ✅ API 키 설정 (대화형)
5. ✅ 테스트 PDF 생성
6. ✅ 종합 테스트 실행

### 스크립트 출력 예시

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  RAGKit 자동 설치 스크립트
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

[1/6] Python 버전 확인...
✅ Python 3.11.5 확인

[2/6] 가상 환경 설정...
✅ .venv 활성화 완료

[3/6] 패키지 설치...
✅ 모든 패키지 설치 완료

[4/6] API 키 설정...
OpenAI API 키를 입력하세요: sk-...
✅ API 키 저장 완료 (.env)

[5/6] 테스트 PDF 생성...
✅ 20페이지 PDF 생성 완료

[6/6] 종합 테스트 실행...
✅ 모든 테스트 통과!

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  설치 완료! 🎉
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

다음 명령어로 시작하세요:
  source .venv/bin/activate
  python examples/test_light.py
```

---

## 🔧 문제 해결

### 문제 1: Python 버전이 낮음

```bash
# 에러: Python 3.10.x 이하
ERROR: This package requires Python 3.11+

# 해결: pyenv 사용
brew install pyenv
pyenv install 3.11.5
pyenv local 3.11.5
```

### 문제 2: pip install 실패

```bash
# 에러: grpcio 빌드 실패
ERROR: Failed building wheel for grpcio

# 해결: numpy 다운그레이드
pip install "numpy<2"
pip install -e .
```

### 문제 3: API 키 인식 안 됨

```bash
# 확인
python -c "import os; print(os.getenv('OPENAI_API_KEY'))"
# None 출력 시

# 해결
source .venv/bin/activate
export OPENAI_API_KEY='sk-...'
# 또는
echo "OPENAI_API_KEY=sk-..." > .env
```

### 문제 4: ChromaDB 오류

```bash
# 에러: Collection name invalid
ValueError: Expected collection name that contains 3-63 characters...

# 원인: 한글 컬렉션명 사용
service.upsert_text("강의_컬렉션", items)  # ❌

# 해결: 영문/숫자/하이픈/언더스코어만
service.upsert_text("lecture_collection", items)  # ✅
```

### 문제 5: 테스트 실패

```bash
# pytest 실패 시
pytest -v --tb=short

# 특정 테스트만 재실행
pytest tests/test_upsert_text.py::test_basic_upsert -v

# ChromaDB 데이터 삭제 후 재시도
rm -rf test_chroma_data
pytest -v
```

---

## 📞 추가 도움말

### 로그 확인

```bash
# pytest 상세 로그
pytest -v -s

# all_test.py 상세 출력
python all_test.py 2>&1 | tee test_output.log
```

### 환경 초기화

```bash
# 가상 환경 삭제
rm -rf .venv

# ChromaDB 데이터 삭제
rm -rf test_chroma_data demo_chroma_data

# 캐시 삭제
find . -type d -name "__pycache__" -exec rm -rf {} +
find . -type f -name "*.pyc" -delete

# 재설치
python -m venv .venv
source .venv/bin/activate
pip install -e .
```

---

## ✅ 체크리스트

설치가 완료되면 다음을 확인하세요:

- [ ] Python 3.11+ 설치 확인
- [ ] 가상 환경 활성화 확인
- [ ] `pip install -e .` 성공
- [ ] `.env` 파일에 API 키 저장
- [ ] `python verify_setup.py` 통과
- [ ] `python all_test.py` 성공
- [ ] `pytest -v` 15개 테스트 통과

**모두 체크되었다면 설치 완료입니다! 🎉**

---

## 🚀 다음 단계

1. **간단한 예제 실행**
   ```bash
   python examples/test_light.py
   ```

2. **README_KR.md 읽기**
   - API 상세 가이드
   - 파라미터 완전 가이드
   - 실전 예제

3. **자신의 데이터로 테스트**
   ```python
   from ragkit import RAGService
   
   service = RAGService()
   # 여기서부터 시작!
   ```

---

**문제가 계속되면 GitHub Issues에 문의하세요.**

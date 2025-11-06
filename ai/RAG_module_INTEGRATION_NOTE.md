# RAG module 통합 노트

위치
- 로컬에 복제됨: `module_intergration/cap1_RAG_module`
- 핵심 폴더: `cap1_RAG_module/ragkit`

확인한 핵심 파일(요약)
- `ragkit/__init__.py`, `ragkit/service.py`, `ragkit/models.py`, `ragkit/config.py`
- 임베딩 관련: `ragkit/embeddings/openai.py`
- vectordb 래퍼: `ragkit/vectordb/chroma.py`
- 유틸: `ragkit/utils/pdf.py`, `ragkit/utils/text.py`
- 테스트/데모: `all_test.py`, `tests/` (존재 시)
- README: `cap1_RAG_module/README.md` (사용법/설치/테스트 설명 포함)

핵심 요지
- `ragkit` 폴더가 이 모듈의 핵심 라이브러리입니다. 다른 모듈에서 사용하려면
  1) 전체 저장소를 유지한 채 `pip install -e ./cap1_RAG_module` 처럼 editable 설치하거나
  2) `ragkit` 폴더만 추출해 프로젝트의 패키지로 포함시키는 방법이 있습니다.

권장: 처음 통합 시에는 전체 레포를 보관하는 편이 안전합니다(테스트 스크립트, requirements, 예제 코드 보존).

환경 (README 기준 권장)
- Python 3.11 이상
- OpenAI API 키 필요 (환경변수 `OPENAI_API_KEY`)
- 개발 시 가상환경 사용 권장

빠른 설정(권장)

```bash
cd module_intergration/cap1_RAG_module
python -m venv .venv
source .venv/bin/activate
pip install -e .
export OPENAI_API_KEY="sk-..."
# (선택) 전체 테스트 실행: python all_test.py
```

통합 옵션 및 고려사항
- 배포형(권장): RAG 모듈을 별도 마이크로서비스(FastAPI 등)로 띄운 뒤 Spring에서 HTTP로 호출
  - 장점: 언어/런타임 분리(Java/Spring ↔ Python), 독립적인 스케일링, 의존성 충돌 회피
  - 단점: 네트워크 호출 추가(지연/오버헤드)

- 라이브러리형: Spring 애플리케이션과 같은 repo 안에서 Python 코드로 직접 임포트하거나, 별도 파이썬 인터프리터로 호출
  - 장점: 네트워크 오버헤드 없음
  - 단점: 빌드/배포 파이프라인 복잡성(특히 Java 애플리케이션 내 Python 의존성 관리)

권장 순서
1. 우선 저장소를 보관하고 `ragkit` 동작/테스트를 로컬에서 확인
2. 통합 전략(마이크로서비스 vs 라이브러리)을 결정
3. 마이크로서비스 선택 시: 간단한 FastAPI wrapper + Dockerfile 생성 권장
4. 라이브러리형 선택 시: `pip install -e` 또는 mono-repo에서 패키지로 포함

다음 단계 제안
- (A) 원하시면 `ragkit`만 별도 `modules/ragkit` 폴더로 추출해 드립니다.
- (B) FastAPI wrapper + Dockerfile 템플릿을 만들어 서비스 형태로 띄우는 작업을 할 수 있습니다.
- (C) 통합 테스트(간단한 upsert/retrieve flow)를 작성해 Spring과의 통신 인터페이스(HTTP contract)를 정의할 수 있습니다.

참고: README에 설치/테스트 절차가 상세히 적혀 있으니, 실제 실행 전에는 README의 권장 Python 버전과 `requirements.txt`(또는 setup.py)를 확인하세요.

---
파일 생성 시점: 2025-10-30
출처: https://github.com/nongman25/cap1_RAG_module (로컬 복제본)

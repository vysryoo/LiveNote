"""
QA 생성용 프롬프트 템플릿

프롬프트 구성 요소:
- section_summary: 현재 강의 내용 (질문 생성 대상)
- rag_context: 강의 자료 조각·이전 구간 요약 (용어 확인용, 직접 출제 금지)
- scope_rule: 출제 범위 제한 (현재 강의에서 말한 내용만 근거)
- context_qp: 기존 질문 (중복 방지용)
"""


class PromptTemplates:
    """유형별 프롬프트 템플릿"""

    # 강의 자료에는 아직 설명하지 않은 뒷부분 내용도 들어 있어, 그 내용으로 출제하지 않도록 제한함
    SCOPE_RULE = """━━━ 출제 범위 ━━━
- 질문과 답변은 '현재 강의'에 나온 내용만 근거로 함
- 참고 자료에만 있는 개념·세부 내용은 질문과 답변에 넣지 않음
- 응용·비교·심화 질문도 현재 강의에서 언급한 개념 안에서 만듦
- 현재 강의가 주제나 학습 목표 소개뿐이면, 소개된 범위(무엇을 왜 배우는지) 안에서만 질문함"""
    
    # 개념 질문 프롬프트
    QA_CONCEPT = """━━━ 현재 강의 (여기서만 질문 생성) ━━━
{section_summary}

{rag_context}

{context_qp}

{scope_rule}

{subject_context}위 기존 질문과 중복되지 않게, 현재 강의에서 핵심 개념/정의 질문 1개만 생성. 답변 5-6문장. 다른 유형(비교/응용/심화 등)을 섞지 말 것.

{language_instruction}

출력 형식 (정확히 이 형식만, JSON·머리말 없이):
첫 줄: 질문 내용
둘째 줄부터: 답변 내용"""

    # 응용 질문 프롬프트
    QA_ADVANCED = """━━━ 현재 강의 (여기서만 질문 생성) ━━━
{section_summary}

{rag_context}

{context_qp}

{scope_rule}

{subject_context}위 기존 질문과 중복되지 않게, 현재 강의의 실제 적용/예시 질문 1개만 생성. 답변 5-6문장.

{language_instruction}

출력 형식 (정확히 이 형식만, JSON·머리말 없이):
첫 줄: 질문 내용
둘째 줄부터: 답변 내용"""

    # 비교 질문 프롬프트
    QA_COMPARISON = """━━━ 현재 강의 (여기서만 질문 생성) ━━━
{section_summary}

{rag_context}

{context_qp}

{scope_rule}

{subject_context}위 기존 질문과 중복되지 않게, 현재 강의의 개념들 비교/대조 질문 1개만 생성. 답변 5-6문장. 다른 유형(개념/바교/심화 등)을 섞지 말 것.

{language_instruction}

출력 형식 (정확히 이 형식만, JSON·머리말 없이):
첫 줄: 질문 내용
둘째 줄부터: 답변 내용"""

    # 심화 질문 프롬프트
    QA_DEEP = """━━━ 현재 강의 (여기서만 질문 생성) ━━━
{section_summary}

{rag_context}

{context_qp}

{scope_rule}

{subject_context}위 기존 질문과 중복되지 않게, 현재 강의의 원리/이유 심화 질문 1개만 생성. 답변 5-6문장. 다른 유형(개념/응용/심화 등)을 섞지 말 것.

{language_instruction}

출력 형식 (정확히 이 형식만, JSON·머리말 없이):
첫 줄: 질문 내용
둘째 줄부터: 답변 내용"""

    # 실습 질문 프롬프트
    QA_PROBLEM = """━━━ 현재 강의 (여기서만 질문 생성) ━━━
{section_summary}

{rag_context}

{context_qp}

{scope_rule}

{subject_context}위 기존 질문과 중복되지 않게, 현재 강의의 실습 문제 1개만 생성. 구체적 수치/상황 제시. 답변 5-6문장. 다른 유형(비교/응용/개념 등)을 섞지 말 것.

{language_instruction}

출력 형식 (정확히 이 형식만, JSON·머리말 없이):
첫 줄: 질문 내용
둘째 줄부터: 답변 내용"""

    @classmethod
    def get_prompt(cls, question_type: str) -> str:
        """질문 유형에 맞는 프롬프트 반환"""
        type_map = {
            "개념": cls.QA_CONCEPT,
            "응용": cls.QA_ADVANCED,
            "비교": cls.QA_COMPARISON,
            "심화": cls.QA_DEEP,
            "실습": cls.QA_PROBLEM,
        }
        return type_map.get(question_type, cls.QA_CONCEPT)
    
    @classmethod
    def build_rag_context(cls, rag_context) -> str:
        """RAG 컨텍스트를 프롬프트 형식으로 변환"""
        if not rag_context or not rag_context.chunks:
            return ""
        
        parts = ["━━━ 참고 자료 (강의 자료·이전 구간. 아직 다루지 않은 내용 포함, 용어 확인용) ━━━"]
        for i, chunk in enumerate(rag_context.chunks[:3], 1):  # 최대 3개
            parts.append(f"{i}. {chunk.text}")
        
        return "\n".join(parts)
    
    @classmethod
    def build_context_qp(cls, previous_qa) -> str:
        """이전 QA를 프롬프트 형식으로 변환 (중복 방지용)"""
        if not previous_qa:
            return ""
        
        parts = ["━━━ 기존 질문 (중복 금지) ━━━"]
        for i, qa in enumerate(previous_qa[-3:], 1):  # 최근 3개
            parts.append(f"{i}. [{qa.type}] {qa.question}")
        
        return "\n".join(parts)
    
    @classmethod
    def build_subject_context(cls, subject: str) -> str:
        """과목 정보를 컨텍스트 형식으로 변환"""
        if not subject:
            return ""
        return f"[과목: {subject}] "
    
    @classmethod
    def build_language_instruction(cls, language: str) -> str:
        """언어 설정을 지시문으로 변환"""
        if not language:
            return ""
        
        # 한국어 처리
        if language.lower() in ["ko", "korean", "한국어"]:
            return "질문과 답변을 한국어로 작성하세요."
        # 영어 처리
        elif language.lower() in ["en", "english", "영어"]:
            return "Write questions and answers in English."
        # 기타 언어
        else:
            return f"Write questions and answers in {language}."

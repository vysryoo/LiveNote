"""
스트리밍 응답을 질문과 답변으로 나누는 파서

모델 출력 형식: 첫 줄은 질문, 이후 줄은 답변.
모델이 형식 지시와 달리 붙이는 머리말("질문:", "Q:", "답변:", "A:" 등)과 강조 기호(**)는 제거한다.
"""

import re
from typing import List, Optional, Tuple

QUESTION_LABEL = re.compile(r"^\s*(?:\*\*)?\s*(?:질문|Q|q)\s*[:.：]\s*(?:\*\*)?\s*")
ANSWER_LABEL = re.compile(r"^\s*(?:\*\*)?\s*(?:답변|A|a)\s*[:.：]\s*(?:\*\*)?\s*")

# 답변 머리말 여부를 판단하기 위해 답변 앞부분을 모아 두는 글자 수. 가장 긴 머리말("**답변:**")보다 길어야 함
ANSWER_LABEL_LOOKAHEAD = 10

Event = Tuple[str, str]


class QAStreamParser:
    """모델 출력 조각을 받아 질문 완성 이벤트와 답변 조각 이벤트로 바꾼다."""

    def __init__(self) -> None:
        self._buffer = ""
        self._question: Optional[str] = None
        self._answer_started = False
        self._answer_parts: List[str] = []

    @property
    def question(self) -> str:
        return self._question or ""

    @property
    def answer(self) -> str:
        return "".join(self._answer_parts).strip()

    def feed(self, delta: str) -> List[Event]:
        """모델 출력 조각을 추가하고 새로 확정된 이벤트를 반환한다.

        Args:
            delta: 모델 출력 조각
        Returns:
            ("question", 질문 전체) 또는 ("answer", 답변 조각) 이벤트 목록. 확정된 내용이 없으면 빈 목록
        """
        self._buffer += delta
        events: List[Event] = []

        if self._question is None:
            question_line = self._take_question_line()
            if question_line is None:
                return events
            self._question = question_line
            events.append(("question", question_line))

        events.extend(self._take_answer())
        return events

    def finish(self) -> List[Event]:
        """출력이 끝났을 때 남은 내용을 이벤트로 반환한다.

        Returns:
            남아 있던 질문 또는 답변 이벤트 목록
        """
        events: List[Event] = []
        if self._question is None:
            # 줄바꿈 없이 끝난 출력은 전체를 질문으로 봄
            line = _strip_question_label(self._buffer)
            self._buffer = ""
            if line:
                self._question = line
                events.append(("question", line))
            return events
        if self._buffer:
            events.extend(self._emit_answer(self._buffer, final=True))
            self._buffer = ""
        return events

    def _take_question_line(self) -> Optional[str]:
        # 질문 앞의 빈 줄은 건너뛰고, 내용이 있는 첫 줄이 끝날 때까지 기다림
        while "\n" in self._buffer:
            line, self._buffer = self._buffer.split("\n", 1)
            line = _strip_question_label(line)
            if line:
                return line
        return None

    def _take_answer(self) -> List[Event]:
        if not self._answer_started:
            pending = self._buffer.lstrip()
            if len(pending) < ANSWER_LABEL_LOOKAHEAD and "\n" not in pending:
                return []
        events = self._emit_answer(self._buffer, final=False)
        self._buffer = ""
        return events

    def _emit_answer(self, text: str, final: bool) -> List[Event]:
        if not self._answer_started:
            text = ANSWER_LABEL.sub("", text.lstrip(), count=1)
            if not text and not final:
                return []
            self._answer_started = True
        if not text:
            return []
        self._answer_parts.append(text)
        return [("answer", text)]


def _strip_question_label(line: str) -> str:
    stripped = QUESTION_LABEL.sub("", line.strip(), count=1)
    return stripped.strip().strip("*").strip()

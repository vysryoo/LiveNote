"""
QA 생성 그래프 (LangGraph)

START → (질문 유형마다 Send) → generate_item → END

질문 유형별 생성은 같은 단계에서 동시에 실행된다. 각 생성 노드는 진행 이벤트를
get_stream_writer()로 내보내고, 호출 쪽은 stream_mode="custom"으로 도착 순서대로 받는다.
"""

from typing import List, Tuple, TypedDict

from langgraph.config import get_stream_writer
from langgraph.graph import END, START, StateGraph
from langgraph.types import Send

from .stream_parser import QAStreamParser


class QAGraphState(TypedDict):
    """그래프 입력: 생성할 항목 목록."""

    items: List[Tuple[str, str]]


class QAItemState(TypedDict):
    """생성 노드 하나가 받는 항목."""

    item: int
    q_type: str
    prompt: str


def build_qa_graph(client):
    """질문 유형별로 동시에 생성하며 진행 이벤트를 내보내는 그래프를 만든다.

    입력 상태는 {"items": [(질문 유형, 프롬프트), ...]}이고, item 번호는 목록 순서(0부터)다.
    내보내는 이벤트는 (이벤트 타입, 질문 유형, 페이로드) 튜플이다.
    - start: 생성 시작 {"item"}
    - question: 질문 완성 {"item", "text"}
    - answer: 답변 조각 {"item", "text"}
    - qa: 생성 완료 {"item", "type", "question", "answer"}
    - error: 생성 실패 {"item", "error"}. 이 항목의 qa 이벤트는 오지 않음

    Args:
        client: stream_text(prompt)로 모델 출력 조각을 내주는 LLM 클라이언트
    Returns:
        컴파일한 LangGraph 그래프
    """

    async def generate_item(state: QAItemState) -> dict:
        write = get_stream_writer()
        item, q_type = state["item"], state["q_type"]
        # 한 항목이 실패해도 다른 항목은 계속 생성되도록 예외를 노드 밖으로 내보내지 않음
        try:
            write(("start", q_type, {"item": item}))
            parser = QAStreamParser()
            async for delta in client.stream_text(state["prompt"]):
                for kind, text in parser.feed(delta):
                    write((kind, q_type, {"item": item, "text": text}))
            for kind, text in parser.finish():
                write((kind, q_type, {"item": item, "text": text}))

            if not parser.question or not parser.answer:
                write(("error", q_type, {"item": item, "error": "질문 또는 답변이 비어 있음"}))
            else:
                write(("qa", q_type, {
                    "item": item,
                    "type": q_type,
                    "question": parser.question,
                    "answer": parser.answer,
                }))
        except Exception as exc:
            write(("error", q_type, {"item": item, "error": str(exc)}))
        return {}

    def fan_out(state: QAGraphState) -> List[Send]:
        return [
            Send("generate_item", {"item": item, "q_type": q_type, "prompt": prompt})
            for item, (q_type, prompt) in enumerate(state["items"])
        ]

    graph = StateGraph(QAGraphState)
    graph.add_node("generate_item", generate_item)
    graph.add_conditional_edges(START, fan_out, ["generate_item"])
    graph.add_edge("generate_item", END)
    return graph.compile()

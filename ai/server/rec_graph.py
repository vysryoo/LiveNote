"""
자료 추천 그래프 (LangGraph)

START → (자료 종류마다 Send) → recommend_one → END

자료 종류별 추천(논문, 위키, 영상, 블로그)은 같은 단계에서 동시에 실행되고, 각 노드는 끝나는 대로
결과를 콜백으로 보낸다. 종류별 추천 내부(검색어 생성, 검색, 거르기, 검증)는 각 모듈 서비스가 맡는다.
"""
from __future__ import annotations

import logging
from typing import Awaitable, Callable, List, TypedDict

from langchain_core.runnables import RunnableConfig
from langgraph.graph import END, START, StateGraph
from langgraph.types import Send

from .models import ResourceType

logger = logging.getLogger(__name__)

# 자료 종류 하나를 추천하고 콜백까지 보내는 함수. 실패도 이 안에서 처리해야 함
RunProvider = Callable[[ResourceType], Awaitable[None]]


class RecGraphState(TypedDict):
    """그래프 입력: 추천할 자료 종류 목록."""

    resource_types: List[ResourceType]


class RecItemState(TypedDict):
    """추천 노드 하나가 받는 자료 종류."""

    resource_type: ResourceType


async def _recommend_one(state: RecItemState, config: RunnableConfig) -> dict:
    run_provider: RunProvider = config["configurable"]["run_provider"]
    # 노드에서 예외가 나가면 그래프가 같은 단계의 다른 자료 종류까지 취소하므로 여기서 막음
    try:
        await run_provider(state["resource_type"])
    except Exception:
        logger.exception("자료 추천 노드 실패: %s", state["resource_type"])
    return {}


def _fan_out(state: RecGraphState) -> List[Send]:
    return [Send("recommend_one", {"resource_type": resource_type}) for resource_type in state["resource_types"]]


def build_rec_graph():
    """자료 종류별 추천을 동시에 실행하는 그래프를 만든다.

    실행 시 config={"configurable": {"run_provider": RunProvider}}로 요청별 추천 함수를 넘긴다.

    Returns:
        컴파일한 LangGraph 그래프
    """
    graph = StateGraph(RecGraphState)
    graph.add_node("recommend_one", _recommend_one)
    graph.add_conditional_edges(START, _fan_out, ["recommend_one"])
    graph.add_edge("recommend_one", END)
    return graph.compile()


rec_graph = build_rec_graph()


async def run_recommendations(resource_types: List[ResourceType], run_provider: RunProvider) -> None:
    """자료 종류별 추천을 동시에 실행하고 모두 끝날 때까지 기다린다.

    Args:
        resource_types: 추천할 자료 종류 목록
        run_provider: 자료 종류 하나를 추천하고 콜백까지 보내는 함수. 예외를 내지 않아야 함
    """
    await rec_graph.ainvoke(
        {"resource_types": resource_types}, config={"configurable": {"run_provider": run_provider}}
    )

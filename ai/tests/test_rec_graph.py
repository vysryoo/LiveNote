from __future__ import annotations

import asyncio

import pytest

from core.schemas import ResourceType
from server.rec_graph import run_recommendations

pytestmark = pytest.mark.anyio("asyncio")


async def test_resource_types_run_concurrently_and_report_as_each_finishes():
    delays = {ResourceType.PAPER: 0.05, ResourceType.WIKI: 0.01, ResourceType.VIDEO: 0.03}
    finished = []

    async def run_provider(resource_type):
        await asyncio.sleep(delays[resource_type])
        finished.append(resource_type)

    started = asyncio.get_running_loop().time()
    await run_recommendations(list(delays), run_provider)
    elapsed = asyncio.get_running_loop().time() - started

    assert finished == [ResourceType.WIKI, ResourceType.VIDEO, ResourceType.PAPER]
    assert elapsed < sum(delays.values())


async def test_unexpected_error_in_one_type_does_not_cancel_others():
    finished = []

    async def run_provider(resource_type):
        if resource_type == ResourceType.PAPER:
            raise RuntimeError("예상하지 못한 오류")
        await asyncio.sleep(0.02)
        finished.append(resource_type)

    await run_recommendations([ResourceType.PAPER, ResourceType.WIKI, ResourceType.BLOG], run_provider)

    assert sorted(finished, key=lambda t: t.value) == sorted([ResourceType.WIKI, ResourceType.BLOG], key=lambda t: t.value)

from __future__ import annotations

import asyncio
import gc

import pytest

from core import tasks

pytestmark = pytest.mark.anyio("asyncio")


async def test_background_task_runs_to_completion_without_caller_reference():
    done = asyncio.Event()

    async def job():
        await asyncio.sleep(0.01)
        done.set()

    tasks.run_in_background(job(), name="job")
    gc.collect()
    await asyncio.wait_for(done.wait(), timeout=1)
    await asyncio.sleep(0)

    assert tasks.running_count() == 0


async def test_failed_task_is_logged_and_released(caplog):
    async def broken():
        raise RuntimeError("실패")

    task = tasks.run_in_background(broken(), name="broken")
    await asyncio.gather(task, return_exceptions=True)
    await asyncio.sleep(0)

    assert tasks.running_count() == 0
    assert "broken" in caplog.text


async def test_shutdown_waits_for_short_tasks_and_cancels_long_ones():
    finished = []

    async def short():
        await asyncio.sleep(0.01)
        finished.append("short")

    async def long():
        await asyncio.sleep(10)
        finished.append("long")

    tasks.run_in_background(short(), name="short")
    long_task = tasks.run_in_background(long(), name="long")
    await tasks.shutdown(timeout_sec=0.1)

    assert finished == ["short"]
    assert long_task.cancelled()
    assert tasks.running_count() == 0

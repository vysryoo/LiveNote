"""
FastAPI 실행 엔트리포인트
"""
from __future__ import annotations

from core.logs import setup_logging

from .app import create_app

setup_logging()
app = create_app()

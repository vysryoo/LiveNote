"""
FastAPI 실행 엔트리포인트
"""
from __future__ import annotations

from .app import create_app

app = create_app()

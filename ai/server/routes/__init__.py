"""
FastAPI 라우터 모음
"""

from .rag import router as rag_router
from .qa import router as qa_router
from .rec import router as rec_router

__all__ = ["rag_router", "qa_router", "rec_router"]

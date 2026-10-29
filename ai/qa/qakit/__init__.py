"""
QAKit - AI 기반 실시간 질문/답변 생성 모듈

LiveNote 프로젝트를 위한 병렬 QA 생성 모듈
"""

__version__ = "1.0.0"
__author__ = "LiveNote Team"

from .service import QAService
from .models import QARequest, QAResponse

__all__ = ["QAService", "QARequest", "QAResponse"]

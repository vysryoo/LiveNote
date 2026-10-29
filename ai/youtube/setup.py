"""
YouTubeKit - 강의 섹션 맞춤 유튜브 추천 모듈
LiveNote 프로젝트를 위한 YouTube Data API 기반 동영상 추천 시스템
"""
from setuptools import setup, find_packages

setup(
    name="youtubekit",
    version="0.1.0",
    description="YouTube recommender for lecture sections (search, summarize, verify)",
    author="LiveNote Team",
    author_email="",
    packages=find_packages(),
    python_requires=">=3.10",
    install_requires=[
        "pydantic>=2.0.0",
        "python-dotenv>=1.0.0",
        "httpx>=0.24.0",
        "youtube-transcript-api>=0.6.1",
        "openai>=1.0.0",
        "rapidfuzz>=3.0.0",
    ],
    extras_require={
        "dev": [
            "pytest>=7.0.0",
            "pytest-asyncio>=0.21.0",
        ]
    },
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
    ],
)


"""
OpenAlexKit - 학술 논문 검색 및 추천 모듈
LiveNote 프로젝트를 위한 OpenAlex API 기반 논문 추천 시스템
"""
from setuptools import setup, find_packages

setup(
    name="openalexkit",
    version="0.1.0",
    description="OpenAlex API based academic paper recommendation module for LiveNote",
    author="LiveNote Team",
    author_email="",
    packages=find_packages(),
    python_requires=">=3.11",
    install_requires=[
        "httpx>=0.24.0",
        "pydantic>=2.0.0",
        "openai>=1.0.0",
        "python-dotenv>=1.0.0",
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
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
    ],
)

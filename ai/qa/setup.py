"""
QAKit 패키지 설정
"""

from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as f:
    long_description = f.read()

setup(
    name="qakit",
    version="1.0.0",
    author="LiveNote Team",
    description="실시간 강의 AI 질문 생성 모듈",
    long_description=long_description,
    long_description_content_type="text/markdown",
    packages=find_packages(),
    python_requires=">=3.11",
    install_requires=[
        "openai>=1.54.0",
        "pydantic>=2.9.0",
        "python-dotenv>=1.0.1",
    ],
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
    ],
)

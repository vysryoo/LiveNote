from setuptools import setup, find_packages

setup(
    name="wikikit",
    version="0.1.0",
    description="Wikipedia document recommendation module for LiveNote",
    author="LiveNote Team",
    packages=find_packages(),
    install_requires=[
        "pydantic>=2.0.0",
        "httpx>=0.27.0",
        "openai>=1.0.0",
        "python-dotenv>=1.0.0",
    ],
    python_requires=">=3.9",
)

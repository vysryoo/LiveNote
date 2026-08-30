from setuptools import setup, find_packages

setup(
    name="googlekit",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "requests>=2.31.0",
        "aiohttp>=3.9.0",
        "pydantic>=2.0.0",
        "python-dotenv>=1.0.0",
        "openai>=1.0.0",
        "python-dateutil>=2.8.0",
    ],
    python_requires=">=3.11",
)

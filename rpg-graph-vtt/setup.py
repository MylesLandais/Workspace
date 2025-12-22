"""Setup script for rpg-graph-vtt package."""

from setuptools import setup, find_packages
from pathlib import Path

# Read README for long description
readme_file = Path(__file__).parent / "README.md"
long_description = readme_file.read_text() if readme_file.exists() else ""

setup(
    name="rpg-graph-vtt",
    version="0.1.0",
    description="Graph-powered D&D 5e character management system with Neo4j",
    long_description=long_description,
    long_description_content_type="text/markdown",
    author="RPG Graph VTT Team",
    license="Apache-2.0",
    packages=find_packages(),
    python_requires=">=3.10,<3.13",
    install_requires=[
        "google-cloud-aiplatform[adk,agent_engine]>=1.93.0",
        "google-adk>=1.0.0",
        "neo4j>=5.0.0",
        "pydantic>=2.0.0",
        "pydantic-settings>=2.8.1",
        "python-dotenv>=1.0.0",
        "fastapi>=0.100.0",
        "uvicorn[standard]>=0.23.0",
    ],
    extras_require={
        "dev": [
            "pytest>=8.3.5",
            "pytest-mock>=3.14.0",
            "pytest-cov>=6.0.0",
            "pytest-asyncio>=0.25.3",
            "jupyter>=1.0.0",
            "ipykernel>=6.0.0",
        ],
    },
)




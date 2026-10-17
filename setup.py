from setuptools import setup, find_packages
from pathlib import Path

this_directory = Path(__file__).parent
long_description = (this_directory / "README.md").read_text(encoding="utf-8") if (this_directory / "README.md").exists() else ""

setup(
    name="volt-ai",
    version="1.0.0",
    description="VOLT-AI: Autonomous Multi-Model AI Coordination, Routing, and Observability Engine",
    long_description=long_description,
    long_description_content_type="text/markdown",
    author="S Sanjai (Baizo)",
    url="https://github.com/baizo7/VOLT",
    license="Apache-2.0",
    packages=find_packages(),
    include_package_data=True,
    entry_points={
        "console_scripts": [
            "volt=cli.main:main",
            "volt-ai=cli.main:main",
            "volt-coder=cli.main:main_coder",
            "observer=cli.main:main",
            "observer-coder=cli.main:main_coder",
        ],
    },
    python_requires=">=3.9",
)

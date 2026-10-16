from setuptools import setup, find_packages

setup(
    name="ai-observer",
    version="1.0.0",
    description="Transparent LLM capture proxy and telemetry observer",
    packages=find_packages(),
    entry_points={
        "console_scripts": [
            "observer=cli.main:main",
            "observer-coder=cli.main:main_coder",
        ],
    },
    python_requires=">=3.9",
)

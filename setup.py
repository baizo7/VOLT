from setuptools import setup, find_packages

setup(
    name="volt-ai",
    version="1.0.0",
    description="VOLT-AI: Intelligent Multi-Model AI Coordination, Routing, and Observability Engine",
    packages=find_packages(),
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

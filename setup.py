from setuptools import setup, find_packages

setup(
    name="gamevcs",
    version="0.1.0",
    description="Version control system for game development",
    packages=find_packages(),
    python_requires=">=3.10",
    install_requires=[
        "fastapi>=0.109.0",
        "uvicorn>=0.27.0",
        "sqlalchemy>=2.0.0",
        "python-jose[cryptography]>=3.3.0",
        "pydantic>=2.5.0",
        "python-multipart>=0.0.6",
        "click>=8.1.0",
        "rich>=13.7.0",
        "questionary>=2.0.0",
        "requests>=2.31.0",
        "gitpython>=3.1.0",
        "xxhash>=3.4.0",
    ],
    entry_points={
        "console_scripts": [
            "gamevcs-server=gamevcs.server.main:main",
            "gamevcs=gamevcs.client.main:cli",
        ],
    },
)

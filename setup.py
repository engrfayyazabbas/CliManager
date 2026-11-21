from setuptools import setup

setup(
    name="agenthub",
    version="1.3.0",
    py_modules=["agenthub"],
    install_requires=[
        "rich>=13.0.0",
    ],
    entry_points={
        "console_scripts": [
            "agenthub=agenthub:main",
        ],
    },
    include_package_data=True,
    package_data={
        "": ["agents.json"],
    },
)

from setuptools import setup

setup(
    name="fixity",
    version="0.1",
    packages=["fixity"],
    entry_points={"console_scripts": ["fixity = fixity.main:main"]}
)

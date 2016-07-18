from setuptools import setup

setup(
    name="fixity",
    version="0.2",
    packages=["fixity"],
    entry_points={"console_scripts": ["fixity = fixity.fixity:main"]}
)

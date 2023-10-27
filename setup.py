from setuptools import setup

setup(
    name="fixity",
    version="0.6.0",
    packages=["fixity"],
    url="https://github.com/artefactual/fixity",
    author="Artefactual Systems",
    author_email="info@artefactual.com",
    entry_points={"console_scripts": ["fixity = fixity.fixity:main"]},
    classifiers=[
        "License :: OSI Approved :: GNU Affero General Public License v3",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
    ],
    python_requires=">=3.8",
)

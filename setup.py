from setuptools import setup

setup(
    name="fixity",
    version="0.4.0",
    packages=["fixity"],
    url="https://github.com/artefactual/fixity",
    author="Artefactual Systems",
    author_email="info@artefactual.com",
    entry_points={"console_scripts": ["fixity = fixity.fixity:main"]},
    classifiers=[
        "License :: OSI Approved :: GNU Affero General Public License v3",
        "Programming Language :: Python :: 2",
        "Programming Language :: Python :: 2.7",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
    ],
    python_requires=">=2.7,!=3.0.*,!=3.1.*,!=3.2.*,!=3.3.*,!=3.4.*,!=3.5.*",
)

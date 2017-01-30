from setuptools import setup

setup(
    name="fixity",
    version="0.3.0",
    packages=["fixity"],
    url = 'https://github.com/artefactual/fixity',
    author = 'Artefactual Systems',
    author_email = 'info@artefactual.com',
    download_url = 'https://github.com/artefactual/fixity/archive/v0.3.0.tar.gz',
    entry_points={"console_scripts": ["fixity = fixity.fixity:main"]},
    classifiers = [
        'License :: OSI Approved :: GNU Affero General Public License v3',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.4',
    ],
)

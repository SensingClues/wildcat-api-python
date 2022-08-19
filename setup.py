import setuptools
import os
import sys



with open("README.md", "r") as fh:
    long_description = fh.read()
with open('requirements.txt') as f:
    required = f.read().splitlines()


setuptools.setup(
    name="wildcatpy",
    version="0.0.1",
    author="sensing_clues",
    author_email="sensingclues@typemail.com",
    description="wildcatpy",
    long_description=long_description,
    url="https://github.com/jobvancreij/wildcat-api-test",
    packages=setuptools.find_packages(),
    install_requires = required,
    include_package_data=True,
    package_dir = {'': 'package'},
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ]
)

import setuptools
import glob
from distutils.command.bdist import bdist as _bdist
from distutils.command.sdist import sdist as _sdist

with open("README.md", "r") as fh:
    long_description = fh.read()
with open('requirements.txt') as f:
    required = f.read().splitlines()
#

setuptools.setup(
    name="wildcatpy",
    version="0.1.0",
    author="sensing_clues",
    author_email="sensingclues@typemail.com",
    description="wildcatpy",
    long_description=long_description,
    url="https://github.com/jobvancreij/wildcat-api-test",
    packages=setuptools.find_packages(),
    data_files=glob.glob('wildcatpy/extractors/**'),
    install_requires = required,
    include_package_data=True,
    package_data={'': ['extractors/*']},
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ]
)

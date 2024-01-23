import glob

import setuptools

with open("readme.md", "r") as fh:
    long_description = fh.read()
with open("requirements.txt") as f:
    required = f.read().splitlines()

setuptools.setup(
    name="wildcatpy",
    version="0.2.0",
    author="sensing_clues",
    author_email="sensingclues@typemail.com",
    description="wildcatpy",
    long_description=long_description,
    url="https://github.com/SensingClues/wildcat-api-python",
    packages=setuptools.find_packages(),
    data_files=glob.glob("wildcatpy/extractors/**"),
    install_requires=required,
    python_requires=">=3.9",
    setup_requires=["pytest-runner"],
    tests_require=["pytest"],
    include_package_data=True,
    package_data={"": ["extractors/*"]},
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
)

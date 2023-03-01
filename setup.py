#!/usr/bin/env python3
from setuptools import setup, find_packages

description = "A collection of useful signal processing and astronomy functionality"

setup(
    name="maggieio_x",
    version="0.0.1.dev",
    url="https://github.com/magao-x/maggieo_x",
    description=description,
    author="Joseph D. Long",
    author_email="me@joseph-long.com",
    packages=["maggieo_x"],
    package_data={
        "maggieo_x": ["default.xml"],
    },
    install_requires=[
        "purepyindi2>=0.0.0",
    ],
    entry_points={
        "console_scripts": [
            "maggieoCtrl=maggieo_x.core:main",
        ],
    },
)

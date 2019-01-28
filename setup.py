#      Markingpy automatic grading tool for Python code.
#      Copyright (C) 2019 University of East Anglia
#
#      This program is free software: you can redistribute it and/or modify
#      it under the terms of the GNU General Public License as published by
#      the Free Software Foundation, either version 3 of the License, or
#      (at your option) any later version.
#
#      This program is distributed in the hope that it will be useful,
#      but WITHOUT ANY WARRANTY; without even the implied warranty of
#      MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#      GNU General Public License for more details.
#
#      You should have received a copy of the GNU General Public License
#      along with this program.  If not, see <https://www.gnu.org/licenses/>.
#
#
from setuptools import setup

with open("README.md", "rt", encoding="utf-8") as f:
    long_description = f.read()
setup(
    name="markingpy",
    author="Sam Morley",
    author_email="sam@inakleinbottle.com",
    version="1.0.0",
    description="Program for automatic grading of Python code.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://markingpy.readthedocs.io/en/latest/index.html",
    packages=["markingpy"],
    install_requires=["pylint"],
    test_suite="tests",
    tests_require=["pytest"],
    python_requires=">=3.6",
    entry_points={"console_scripts": ["markingpy=markingpy.cli:main"]},
    package_data={"markingpy": ["data/markingpy.conf", "data/scheme.py"]},
    classifiers=[
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "License :: OSI Approved :: GNU General Public License v3 (GPLv3)",
        "Operating System :: OS Independent",
    ],
)

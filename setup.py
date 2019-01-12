from setuptools import setup


with open('README.md', 'rt', encoding='utf-8') as f:
    long_description = f.read()

setup(
    name="markingpy",
    author="Sam Morley",
    author_email="sam@inakleinbottle.com",
    version="0.1.0",
    description="Program for automatic grading of Python code.",
    long_description=long_description,
    long_description_content_type='text/markdown',
    url='https://markingpy.readthedocs.io/en/latest/index.html',
    packages=["markingpy"],
    install_requires=["pylint"],
    test_suite="tests",
    tests_require=['pytest'],
    requires_python= '>=3.6.0',
    entry_points={"console_scripts": ["markingpy=markingpy.cli:main"]},
    package_data={"markingpy": ["data/markingpy.conf", "data/scheme.py"]},
    classifiers=[
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "License :: OSI Approved :: GNU General Public License v3 (GPLv3)",
        "Operating System :: OS Independent",
    ]
)

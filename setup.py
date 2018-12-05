#!/usr/bin/env python
from os import environ

from setuptools import Extension, find_packages, setup

# Opt-in to building the C extensions for Python 2 by setting the
# ENABLE_DJB_HASH_CEXT environment variable
if environ.get('ENABLE_DJB_HASH_CEXT'):
    ext_modules = [
        Extension('cdblib._djb_hash', sources=['cdblib/_djb_hash.c']),
    ]
else:
    ext_modules = []


description = "Pure Python reader/writer for Dan J. Berstein's CDB format."

setup(
    author='David Wilson',
    author_email='dw@botanicus.net',
    description=description,
    long_description=description,
    download_url='https://github.com/dw/python-pure-cdb',
    keywords='cdb file format appengine database db',
    license='MIT',
    name='pure-cdb',
    version='2.2.0',
    packages=find_packages(include=['cdblib']),
    ext_modules=ext_modules,
    install_requires=['six>=1.0.0,<2.0.0'],
    test_suite='tests',
    tests_require=['flake8'],
    entry_points={
        'console_scripts': [
            'python-pure-cdbmake=cdblib.cdbmake:main',
            'python-pure-cdbdump=cdblib.cdbdump:main',
        ],
    },
)

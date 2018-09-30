#!/usr/bin/env python

from setuptools import Extension, find_packages, setup

_cdblib_module = Extension('cdblib._cdblib', sources=['cdblib/_cdblib.c'])

setup(
    author='David Wilson',
    author_email='dw@botanicus.net',
    description="Pure Python reader/writer for Dan J. Berstein's CDB format.",
    download_url='https://github.com/dw/python-pure-cdb',
    keywords='cdb file format appengine database db',
    license='MIT',
    name='pure-cdb',
    packages=find_packages(include=['cdblib']),
    ext_modules=[_cdblib_module],
    install_requires=['six>=1.0.0,<2.0.0'],
    test_suite='tests',
    version='2.0.0'
)

#!/usr/bin/env python

from distutils.core import setup, Extension

_cdblib_module = Extension('_cdblib', sources=['_cdblib.c'])

setup(author='David Wilson',
      author_email='dw@botanicus.net',
      description="Pure Python reader/writer for Dan J. Berstein's CDB format.",
      download_url='https://github.com/dw/python-pure-cdb',
      keywords='cdb file format appengine database db',
      license='MIT',
      name='pure-cdb',
      py_modules=['cdblib'],
      ext_modules=[_cdblib_module],
      version='2.0.0'
)

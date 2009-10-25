#!/usr/bin/env python

from distutils.core import setup

setup(author='David Wilson',
      author_email='dw@botanicus.net',
      description="Pure Python reader/writer for Dan J. Berstein's CDB format.",
      download_url='http://code.google.com/p/python-pure-cdb/',
      include_package_data=True,
      keywords='cdb file format appengine database db',
      license='MIT',
      name='pure-cdb',
      py_modules=['cdblib'],
      version='1.0',
      zip_safe=False)

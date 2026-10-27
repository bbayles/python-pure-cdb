from os import environ

from setuptools import Extension, setup

# Opt-in to building the C extension by setting the
# ENABLE_DJB_HASH_CEXT environment variable
if environ.get('ENABLE_DJB_HASH_CEXT', '1') != '0':
    ext_modules = [
        Extension('cdblib._djb_hash', sources=['cdblib/_djb_hash.c']),
    ]
else:
    ext_modules = []

setup(ext_modules=ext_modules)

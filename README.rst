python-pure-cdb
===============

.. image:: https://github.com/bbayles/python-pure-cdb/actions/workflows/python-app.yml/badge.svg
    :target: https://github.com/bbayles/python-pure-cdb/actions/workflows/python-app.yml

**Full featured constant database reader, and writer**

**Compatible with D.J. Bernstein's cdb**

A constant database is a of key-value database, a mapping - that can
not be changed at runtime. That restriction allows to use a perfect
hash that makes retrieval much faster than a regular key-value store.

`pure-cdb` will read the files that are produced by the original tool
written by D.J. Bernstein. It also support a 64-bit setting to avoid
the restriction in the original design of 4-GiB database files.

This package works with most common CPython versions, and PyPy.

For a version that works with Python 2, see `this older release
<https://github.com/dw/python-pure-cdb/releases/tag/v2.2.0>`_.  To aid
in porting `cdb` applications to Python 3, this library provides a
compatability module for the `python-cdb
<https://github.com/acg/python-cdb>`_ package, which can act as a
drop-in replacement (see `the docs
<https://python-pure-cdb.readthedocs.io>`_).

For more information on constant databases, see `djb's page
<https://cr.yp.to/cdb.html>`_ and `Wikipedia
<https://en.wikipedia.org/wiki/Cdb_(software)>`_.

The documentation for this package is available at
`https://python-pure-cdb.readthedocs.io
<https://python-pure-cdb.readthedocs.io>`_.

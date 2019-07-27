python-pure-cdb
===============

.. image:: https://travis-ci.com/bbayles/python-pure-cdb.svg?branch=master
    :target: https://travis-ci.com/bbayles/python-pure-cdb

.. image:: https://readthedocs.org/projects/python-pure-cdb/badge/?version=latest
    :target: https://python-pure-cdb.readthedocs.io/en/latest/?badge=latest

The `python-pure-cdb` package (`pure-cdb <https://pypi.org/project/pure-cdb/>`_ on PyPI)
is a Python library for working with D.J. Bernstein's "constant databases."

In addition to being able to read and write the database files produced by
other `cdb` tools, this package can produce and consume "64-bit"
constant databases that don't have the usual 4 GiB restriction.

This package works with Python 3.4 and above.
For a version that works with Python 2, see `this older release <https://github.com/dw/python-pure-cdb/releases/tag/v2.2.0>`_.
To aid in porting `cdb` applications to Python 3, this library provides a
compatability module for the `python-cdb <https://github.com/acg/python-cdb>`_
package, which can act as a drop-in replacement (see `the docs <https://python-pure-cdb.readthedocs.io>`_).

For more information on constant databases, see `djb's page <https://cr.yp.to/cdb.html>`_
and `Wikipedia <https://en.wikipedia.org/wiki/Cdb_(software)>`_.

The documentation for this package is available at
`https://python-pure-cdb.readthedocs.io <https://python-pure-cdb.readthedocs.io>`_.

Command line tools
==================

The `python-pure-cdb` package contains Python implementations of the
`cdbmake and cdbdump programs <https://cr.yp.to/cdb/cdbmake.html>`_.

`python-pure-cdbmake` should be able to create databases that are compatible
with other implementations, including the standard one.
It can also create "64-bit" databases that don't have the usual 4 GiB
restriction.

Similarly, `python-pure-cdbdump` should be able to read databases produced
by other implementations, including the standard one.
It can also read the "64-bit" databases produced by this package.

`python-pure-cdbmake`
---------------------

This utility creates a database file from text records using the following
format:

.. code-block:: none

    +klen,dlen:key->data

Where:
    * `klen` is the length of `key` (in bytes)
    * `dlen` is the length of `data` (in bytes)
    * `key` can be any string of characters
    * `data` can be any string of characters.

Each record must end with a newline character. For example:

.. code-block:: none

    +1,2:a->bb
    +2,1:aa->b

`python-pure-cdbmake` reads these records from stdin. When invoking the
utility, you have to specify two file paths:

    * The first (`cdb`) is the ultimate location of the database
    * The second (`cdb.tm`) is a temporary location to use when creating the
      database. It will be moved to the ultimate location after completion.

.. code-block:: shell

    $ <records_file.txt python-pure-cdbmake ~/records_db.cdb /tmp/records_db.tmp

Use the `-64` switch to enable "64-bit" mode, which can write larger database
files at the expense of compatibility with other cdb packages.

`python-pure-cdbdump`
---------------------

.. code-block

    python-pure-cdbdump -h
    usage: python-pure-cdbdump [-h] [-64]

    Python version of djb's cdbdump. Supports standard 32-bit cdb files as well as
    64-bit variants.

    optional arguments:
      -h, --help  show this help message and exit
      -64         Use non-standard 64-bit file offsets

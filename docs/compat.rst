python-cdb compatibility module
===============================

`cdblib.compat` is designed to be used as a drop-in replacement for
`python-cdb <https://github.com/acg/python-cdb>`_, a Python 2-only module for
interacting with constant databases.

To use it in your Python 3 application:

.. code-block:: python

    import cdblib.compat as cdb  # replaces import cdb


Reading existing databases
--------------------------

The `init()` function accepts a path to an existing database file. It
returns a `cdb` object that can be used to retrieve records from it.

    >>> db = cdb.init('info.cdb')

The `.each()` method returns successive `(key, value)` pairs from the database.
After the last record is returned the next call will return `None`.
The call after that will return the first record again.

    >>> db.each()
    ('a', 'value_a1')
    >>> db.each()
    ('a', 'value_a2')
    >>> db.each()
    ('b', 'value_b1')
    >>> db.each()  # No more records
    >>> db.each()  # Loop around to the first record
    ('a', 'value_a1')

The `.keys()` method returns a list of distinct keys from the database.

    >>> db.keys()
    ['a', 'b']

The `cdb` object keeps an iterator over the distinct keys of the database.
The `.firstkey()` method resets the iterator and returns the first stored key.
The `.nextkey()` advances the iterator and returns the next key.
After exhausting the iterator, `None` will be returned until `.firstkey()` is
called again.

    >>> db.firstkey()
    'a'
    >>> db.nextkey()
    'b'
    >>> db.nextkey()  # No more keys
    >>> db.firstkey()  # Reset the iterator
    'a'

Call the `.get()` method with a key `k` and an optional index `i` to retrieve
the `i`-th value stored under `k`. If there is no such value, `.get()` returnes
`None`.

    >>> db.get('a')
    'value_a1'
    >>> db.get('a', 1)
    'value_a2'
    >>> db.get('a', 3)  # Returns None

The `cdb` object can be accessed like a `dict` to retrieve the first value
stored under a key. If there is no such key in the database, `KeyError` is
raised.

    >>> db['a']
    'value_a1'
    >>> db['b']
    'value_b1'

Call the `.getall()` method to retrieve a list of the values stored under the
key `k`.

    >>> db.getall('a')
    ['value_a1', 'value_a2']
    >>> db.getall('b')
    ['value_b1']
    >>> db.getall('c')  # No such key, returns empty list
    []

The `cdb` object has a `size` property, which returns the total size of the
database (in bytes). It also has a `name` property, which returns the path
to the database file.


Writing new databases
---------------------

The `cdbmake()` class is used to create a new database. Call it with two
file paths: the first is the ultimate location of the database.
temporary location to use when creating the database.
It will be moved to the ultimate location after completion.

    >>> cdb_path = '/tmp/info.cdb'
    >>> tmp_path = cdb_path + '.tmp'
    >>> db = cdbmake(cdb_path, tmp_path)

Add records to the database with the `.add()` or `.addmany()` methods.

    >>> db.add('b', 'value_b1')
    >>> db.addmany([('a', 'value_a1'), ('a', 'value_a2')])

Write the database structure to disk and rename the temporary file to the
ultimate file with the `.finish()` method.


Notes on encoding
-----------------

Since `python-cdb` is a Python 2-only module, it does not distinguish between
text and binary keys or values.

In order to handle `str` keys and values, `cdblib.compat` encodes text data
on the way into the database:

    >>> new_db.add('text_key', b'\x80 binary data')  # Key is encoded to binary
    >>> new_db.add(b'\x80 binary key', 'text_data')  # Value is encoded to binary

It also decodes text data when reading:

    >>> existing_db.get(b'\x80 binary key')  # Text value is decoded
    'text_data'
    >>> existing_db.get('text_key')  # Binary value is left alone
    b'\x80 binary data'

`utf-8` encoding is used by default in `cdblib.compat.init()` and `cdblib.compat.cdbmake()`.
Pass a different encoding with the `encoding` keyword argument to use a different scheme.
Turn off automatic encoding or decoding by supplying `encoding=None`.

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

The `each()` method returns successive `(key, value)` pairs from the database.
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

The `keys()` method returns a list of distinct keys from the database.

    >>> db.keys()
    ['a', 'b']

The `cdb` object keeps an iterator over the distinct keys of the database.
The `firstkey()` method resets the iterator and returns the first stored key.
The `nextkey()` advances the iterator and returns the next key.
After exhausting the iterator, `None` will be returned until `firstkey()` is
called again.

    >>> db.firstkey()
    'a'
    >>> db.nextkey()
    'b'
    >>> db.nextkey()  # No more keys
    >>> db.firstkey()  # Reset the iterator
    'a'

Call the `get()` method with a key `k` and an optional index `i` to retrieve
the `i`-th value stored under `k`. If there is no such value, `get()` returnes
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

Call the `getall()` method to retrieve a list of the values stored under the
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

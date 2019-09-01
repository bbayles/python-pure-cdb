Getting started
===============

Installation
------------

Install the library with `pip <https://pip.pypa.io/en/stable/>`_:

.. code-block:: shell

    pip install pure-cdb

Once the library is installed, import `cdblib` to use it.

Reading existing cdb files
--------------------------

`cdblib.Reader` can query an existing database.

Pass it a `bytes`-like object of the file's contents to start:

    >>> import cdblib
    >>> with open('info.cdb', 'rb') as f:
    ...     data = f.read()
    >>> reader = cdblib.Reader(data)

`Reader` instances implement a `dict`-like interface. To retrieve everything
stored in the database, use the `.iteritems()` method.

    >>> for key, value in reader.iteritems():
    ...     print('+{},{}:{}->{}'.format(len(key), len(value), key, value))

To retrieve the first value stored at a key, use the `.get()` method.

    >>> reader.get(b'some_key')
    b'some_value'

Note that all keys and values are `bytes` objects.
For more information, see the library documentation.

You may also construct a `Reader` instance with a file path.
Use a `with` block to automatically close the file:

    >>> with cdblib.Reader.from_file_path('info.cdb', 'rb') as reader:
    ...    pass  # Do your thing here

For "64-bit" database files, use `cdblib.Reader64` instead of `cdblib.Reader`.

Writing new cdb files
---------------------

`cdblib.Writer` can create a new database.

Pass it a file-like object (opened in binary write mode) to start.
Then write to the database with the `.put()` method.

   >>> import cdblib
   >>> with open('/tmp/new.cdb', 'wb') as f:
   ...    with cdblib.Writer(f) as f:
   ...        writer.put(b'key', b'value')

As with the reader class, all keys and values are `bytes` objects.

For "64-bit" database files, use `cdblib.Writer64` instead of `cdblib.Writer`.

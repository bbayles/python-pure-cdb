Library reference
=================

The `Reader` classes
--------------------

`cdblib.Reader` reads standard "32-bit" cdb files, such as those produced by the
`cdbmake` CLI tool. `cdblib.Reader64` reads "64-bit" cdb files, which can be
produced by this package.

The `Reader` classes take one positional argument, a `bytes`-like object with
a datbase's content:

    >>> import cdblib
    >>> with open('info.cdb', 'rb') as f:
    ...     data = f.read()
    >>> reader = cdblib.Reader(data)

An `mmap` object can be used to avoid reading an entire database into memory -
see below.

----

The `.items()` method returns a list of `(key, value)` tuples representing
all of the records stored in the database (in insertion order).
Note that a single key can have multiple values associated with it.

    >>> reader.items()
    [(b'k1', b'v1'), (b'k2', b'v2a'), (b'k2', b'v2b')]

The `.iteritems()` is like `.items()`, but it returns an iterator over the
items rather than a list.

The `.keys()` method returns a list of the keys stored in the database
(in insertion order). The `.iterkeys()` method returns an iterator over the
keys.

The `.values()` method returns a list of the values stored in the database
(in insertion order). The `.itervalues()` method returns an iterator over the
values.

----

Calling `len()` on a `Reader` instance returns the number of records (key-value
pairs) stored in the database.

    >>> len(reader)
    3

The `in` operator can be used to test whether a key is present in the datbase

    >>> b'k1` in reader
    True
    >>> b'k3' in reader
    False

---

The `.get(key)` method returns the first value in the database for `key`.

    >>> reader.get(b'k2')
    b'v2b'

The `.gets(key)` method returns an iterator over all the values associated
with `key`.

    >>> list(reader.)gets(b'k2')
    [b'k2a', b'k2b']


Notes on encoding
^^^^^^^^^^^^^^^^^

Limiting memory usage
^^^^^^^^^^^^^^^^^^^^^

Alternate hash functions
^^^^^^^^^^^^^^^^^^^^^^^^

The `Writer` classes
--------------------

Notes on encoding
^^^^^^^^^^^^^^^^^

Alternate hash functions
^^^^^^^^^^^^^^^^^^^^^^^^

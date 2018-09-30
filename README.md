## Introduction

`python-pure-cdb` (`pure-cdb` on [PyPI](https://pypi.org/project/pure-cdb/)) is a Python library for reading and writing djb's "constant database" files. These disk-based associative arrays that allow efficient storage and retrieval of thousands of keys. For more information on `cdb`, see [djb's page](https://cr.yp.to/cdb.html) and [Wikipedia](https://en.wikipedia.org/wiki/Cdb_(software)). 

### Installation and usage

Install `pure-cdb` with `pip`:

```
pip install pure-cdb
```

Then import `cdblib` to access the `Reader` and `Writer` classes.

---

`Reader` provides an interface to a `cdb` file's contents - use the `.iterkeys()` method to iterate over keys, and the `.get()` method to retrieve a key's value.

```python
import cdblib

with open('info.cdb', 'rb') as f:
    data = f.read()

reader = cdblib.Reader(data)

reader.get(b'hello')
```

All keys are `bytes` objects (`str` in Python 2). By default all values are also retrieved as `bytes` objects, but the `.getstring()` and `.getint()` methods can be used to retrieve decoded strings and integers, respectively.

---

`Writer` allows for creating new `cdb` files. Use the `.put()` method to insert a key / value pair, and the `.finalize()` method to create the CDB structure.

```python
with open('/home/bo/Desktop/new.cdb', 'wb') as f:
    writer = cdblib.Writer(f)
    writer.put(b'key', b'value')
    writer.finalize()
```

As with the `Reader` class, keys and values are `bytes` objects. The `.putstrings()` and `.putint()` methods can be used to insert encoded text data and integers, respectively.

---

### Remarks on usage

Constant databases have the desirable property of requiring low overhead to open. This makes them ideal for use in environments where it's not always possible to have data hanging around in RAM awaiting use, for example in a CGI script or Google App Engine.

On App Engine, reading a 700kb database into memory from the filesystem costs around 90ms, after which the cost of individual lookups is negligible (one simple benchmark achieved 94k lookups/sec running on App Engine, and that was using `djb_hash()`). This makes CDBs ideal for storing many small keys that are infrequently accessed, for example in per-language corpora containing 10k+ internationalized strings (my original use case).

The format might also be useful as a composite file storage alternative to the `zipfile` module. Since the Reader interface only requires a file-like object, it is possible to wrap a string stored in a Datastore entity in a `cStringIO` object, allowing convenient access to it as a CDB.

When storing many thousands of keys in a Datastore entity, CDBs might enable you to bypass the "indexed fields" limit of the `Expando` class without resorting to `pickle`, as well as reduce deserialization overhead when only a few keys of such an entity are normally accessed and rarely updated.

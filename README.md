Manipulate DJB's Constant Database files. These are 2 level disk-based hash tables that efficiently handle thousands of keys, while remaining space-efficient.

http://cr.yp.to/cdb.html

Note the Reader class reads the entire CDB into memory.

------

Constant databases have the desirable property of requiring low overhead to open. This makes them ideal for use in environments where it's not always possible to have data hanging around in RAM awaiting use, for example in a CGI script or Google App Engine.

On App Engine, reading a 700kb database into memory from the filesystem costs around 90ms, after which the cost of individual lookups is negligible (one simple benchmark achieved 94k lookups/sec running on App Engine, and that was using `djb_hash()`). This makes CDBs ideal for storing many small keys that are infrequently accessed, for example in per-language corpora containing 10k+ internationalized strings (my original use case).

The format might also be useful as a composite file storage alternative to the `zipfile` module. Since the Reader interface only requires a file-like object, it is possible to wrap a string stored in a Datastore entity in a `cStringIO` object, allowing convenient access to it as a CDB.

When storing many thousands of keys in a Datastore entity, CDBs might enable you to bypass the "indexed fields" limit of the `Expando` class without resorting to `pickle`, as well as reduce deserialization overhead when only a few keys of such an entity are normally accessed and rarely updated.
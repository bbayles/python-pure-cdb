Version history
===============

* `Version 3.1.1 <https://github.com/dw/python-pure-cdb/releases/tag/v3.1.1>`_
    * Fixed a bug with handling hashing errors (thanks to maikroeder)
* `Version 3.1.0 <https://github.com/dw/python-pure-cdb/releases/tag/v3.1.0>`_
    * `Reader` instances now act as context managers, and can be called with file paths or file-like objects.
* `Version 3.0.0 <https://github.com/dw/python-pure-cdb/releases/tag/v3.0.0>`_
    * This package now supports Python 3 only. For a version that works with Python 2, see `this older release <https://github.com/dw/python-pure-cdb/releases/tag/v2.2.0>`_.
    * Added the `python-cdb` compatibility module
* `Version 2.2.0 <https://github.com/dw/python-pure-cdb/releases/tag/v2.2.0>`_
    * Added non-`strict` mode for convenience when using non-binary keys.
    * API docs are now available at ReadTheDocs.
* `Version 2.1.0 <https://github.com/dw/python-pure-cdb/releases/tag/v2.1.0>`_
    * Python 3 support
    * `Writer` and `Writer64` can now act as context managers.
    * A Python implementation of `cdbdump` (`python-pure-cdbdump`) is now included.
    * The Python implementation of `cdbmake` was renamed `python-pure-cdbmake` and some bugs were fixed.

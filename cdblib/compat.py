from itertools import chain, cycle, islice, repeat
from mmap import mmap, ACCESS_READ
from os import rename
from os.path import getsize

from .cdblib import Reader, Writer


class error(IOError):
    pass


class cdbmake:
    def __init__(self, cdb, tmp, encoding='utf-8'):
        """Create a new database to be stored at the path given by
        *cdb*. Records will be written to the file at the path given by
        *tmp*. After the ``finish()`` method is called, the file at *cdb*
        will be replaced by the one at *tmp*.
        If *encoding* is given, ``str`` keys and values will be converted
        to ``bytes`` with the given encoding. If *encoding* is ``None``, only
        ``bytes`` keys and values are accepted.
        """
        self.fn = cdb
        self.fntmp = tmp
        self.encoding = encoding

        self._temp_obj = open(self.fntmp, 'wb')
        self._writer = Writer(self._temp_obj, strict=True)
        self.numentries = 0
        self._finished = False

    def _cleanup(self):
        try:
            self._temp_obj.close()
        except Exception:
            pass

    def __del__(self):
        self._cleanup()

    def add(self, key, data):
        """Store a record in the database.
        """
        if self._finished:
            raise error('cdbmake object already finished')

        args = []
        for arg in (key, data):
            if isinstance(arg, bytes):
                args.append(arg)
            elif isinstance(arg, str) and self.encoding:
                args.append(arg.encode(self.encoding))
            else:
                raise TypeError(
                    'add method only accepts bytes and str objects'
                )

        self._writer.put(*args)
        self.numentries += 1

    def addmany(self, items):
        """Store each of the records in *items* in the the database.
        *items* should be an iterable of ``(key, value)`` pairs.
        """
        for key, value in items:
            self.add(key, value)

    @property
    def fd(self):
        return self._temp_obj.fileno()

    def finish(self):
        """Finalize the database being written to. Then move the temporary
        database to its final location.
        """
        if self._finished:
            return

        self._writer.finalize()
        self._temp_obj.close()
        rename(self.fntmp, self.fn)
        self._finished = True


class cdb:
    def __init__(self, f, encoding='utf-8'):
        self._file_path = f

        self.encoding = encoding
        strict = not bool(encoding)

        self._file_obj = open(self._file_path, mode='rb')
        self._mmap_obj = mmap(self._file_obj.fileno(), 0, access=ACCESS_READ)
        self._reader = Reader(self._mmap_obj, strict=strict)

        self._keys = self._get_key_iterator()
        self._items = cycle(chain(self._decoded_items(), [None]))

    def _cleanup(self):
        for f in (self._mmap_obj, self._file_obj):
            try:
                f.close()
            except Exception:
                pass

    def __del__(self):
        self._cleanup()

    def _unique_keys(self):
        all_keys = (k for k, v in self._decoded_items())
        seen = set()
        seen_add = seen.add
        for k in all_keys:
            if k not in seen:
                seen_add(k)
                yield k

    def _decoded_items(self):
        for pair in self._reader.iteritems():
            if not self.encoding:
                yield pair
            else:
                decoded_pair = []
                for e in pair:
                    try:
                        e = e.decode(self.encoding)
                    except UnicodeDecodeError:
                        pass
                    decoded_pair.append(e)

                yield tuple(decoded_pair)

    def _get_key_iterator(self):
        unique_keys = self._unique_keys()
        return cycle(chain(unique_keys, repeat(None)))

    def each(self):
        """Return successive ``(key, value)`` tuples from the database.
        After the last record is returned, the next call will return ``None``.
        The call after that will return the first record again.
        """
        return next(self._items)

    @property
    def fd(self):
        return self._file_obj.fileno()

    def firstkey(self):
        """Return the first key in the database.
        If ``nextkey()`` is called after ``firstkey()``, the second key will
        returned.
        """
        self._keys = self._get_key_iterator()
        return next(self._keys)

    def get(self, k, i=0):
        """Return the ``i``-th value stored under the key given by ``k``.
        If there are fewer than ``i`` items stored under key ``k``, return
        ``None``.
        """
        value = next(islice(self._reader.gets(k), i, i + 1), None)
        if not self.encoding:
            return value

        try:
            return value.decode(self.encoding)
        except (AttributeError, UnicodeDecodeError):
            return value

    def __getitem__(self, key):
        value = self.get(key)
        if value is None:
            raise KeyError(key)

        return value

    def getall(self, k):
        """Return a list of the values stored under key ``k``.
        """
        ret = []
        ret_append = ret.append
        for value in self._reader.gets(k):
            try:
                value = value.decode(self.encoding)
            except (AttributeError, UnicodeDecodeError, TypeError):
                value = value
            ret_append(value)

        return ret

    def keys(self):
        """Return a list of the distinct keys stored in the database.
        """
        unique_keys = self._unique_keys()
        return list(unique_keys)

    @property
    def name(self):
        return self._file_path

    def nextkey(self):
        """Return the next key in the datbase, or ``None`` if there are no more
        keys to retrieve. Call ``firstkey()`` to start from the beginning
        again.
        """

        return next(self._keys)

    @property
    def size(self):
        return getsize(self._file_path)


def init(f, encoding='utf-8'):
    """Return a ``cdb`` object based on the database stored at the file path
    given by *f*.
    If *encoding* is given, retrieved keys and values will be decoded using
    the given encoding (if possible).
    """
    return cdb(f, encoding=encoding)

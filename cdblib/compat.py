from itertools import islice
from mmap import mmap, ACCESS_READ

from .cdblib import Reader, Writer


class cdbmake:
    def __init__(self, cdb, tmp):
        self.fn = cdb
        self.fntmp = tmp

    def add(self, key, data):
        pass

    def addmany(self, items):
        pass

    @property
    def fd(self):
        pass

    def finish(self):
        pass

    @property
    def numentries(self):
        pass


class cdb:
    def __init__(self, f):
        self._file_path = f
        self._file_obj = open(self._file_path, mode='rb')
        self._mmap_obj = open(self._file_obj.fileno(), 0, access=ACCESS_READ)
        self._reader = Reader(self._mmap_obj)
        self._keys = self._reader.iterkeys()
        self._items = self._reader.iteritems()

    def each():
        ret = next(self._items, None)
        if ret is None:
            self._items = self._reader.iteritems()
            ret = next(self._items, None)

        return ret

    @property
    def fd(self):
        return self._file_obj.fileno()

    def firstkey(self):
        return next(self._reader.iterkeys(), None)

    def get(self, k, i=0):
        it = next(islice(self._reader.gets(k), i, i + 1), None)

    def getall(self, k):
        return list(self._reader.gets(k))

    def keys(self):
        return self._reader.keys()

    @property
    def name(self):
        return self._file_path

    def nextkey(self):
        ret = next(self._keys, None)
        if ret is None:
            self._items = self._reader.iterkeys()
            ret = next(self._keys, None)

        return ret

    @property
    def size(self):
        return self._reader.length

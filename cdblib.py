#!/usr/bin/env python2.5

'''
Manipulate DJB's Constant Database files. These are 2 level disk-based hash
tables that efficiently handle thousands of keys, while remaining
space-efficient.

    http://cr.yp.to/cdb.html

Note the Reader class reads the entire CDB into memory. When using Writer,
consider using Python's hash() instead of cdb_hash() for a tidy 28% speedup,
however readers must be similarly configured.
'''

import _struct
from itertools import chain


UNSPECIFIED = [None]

def cdb_hash(s):
    h = 5381
    for c in s:
        h = (((h << 5) + h) ^ ord(c)) & 0xffffffff
    return h # for small strings, masking here is faster.

read_2_le4 = _struct.Struct('<LL').unpack
write_2_le4 = _struct.Struct('<LL').pack


class Reader(object):
    __slots__ = ('data', '_index', 'hash')

    def __init__(self, fp, hash=cdb_hash):
        self.data = fp.read()
        if len(self.data) < 2048:
            raise IOError('CDB too small')

        self.hash = hash

    def _get_value(self, pos, key):
        klen, dlen = read_2_le4(self.data[pos:pos+8])
        pos += 8

        if self.data[pos:pos+klen] == key:
            pos += klen
            return self.data[pos:pos+dlen]

    def gets(self, key):
        h = self.hash(key)
        idx = (h << 3) & 2047
        start, nslots = read_2_le4(self.data[idx:idx+8])

        if nslots:
            end = start + (nslots << 3)
            slot_off = start + (((h >> 8) % nslots) << 3)

            for pos in chain(xrange(slot_off, end, 8),
                             xrange(start, slot_off, 8)):
                rec_h, rec_pos = read_2_le4(self.data[pos:pos+8])

                if not rec_h:
                    break
                elif rec_h == h:
                    value = self._get_value(rec_pos, key)
                    if value is not None:
                        yield value

    def get(self, key, default=UNSPECIFIED):
        if default is UNSPECIFIED:
            try:
                return self.gets(key).next()
            except StopIteration:
                raise KeyError(key)

        # Avoid exception catch when handling default case; much faster.
        return chain(self.gets(key), (default,)).next()

    __getitem__ = get

    def getint(self, key, default=UNSPECIFIED):
        return int(self.get(key, default), 10)

    def getints(self, key):
        return (int(v, 10) for v in self.gets(key))

    def getstring(self, key, default=UNSPECIFIED):
        return self.get(key, default).decode('utf-8')

    def getstrings(self, key):
        return (v.decode('utf-8') for v in self.gets(key))


class Writer(object):
    def __init__(self, fp, hash=cdb_hash):
        self.fp = fp
        self.hash = hash

        self._curslab = []
        self._slabs = [self._curslab]

        self._index = [0, 0] * 256
        self._write_index()

    def _write_index(self):
        index = self._index

        self.fp.seek(0)
        for i in range(0, 512, 2):
            self.fp.write(write_2_le4(index[i], index[i+1]))

    def put(self, key, value):
        assert type(key) is str and type(value) is str

        pos = self.fp.tell()
        self.fp.write(write_2_le4(len(key), len(value)))
        self.fp.write(key)
        self.fp.write(value)

        if len(self._curslab) == 1000:
            self._curslab = []
            self._slabs.append(self._curslab)

        self._curslab.append((self.hash(key), pos))

    def putint(self, key, value):
        self.put(key, str(value))

    def putints(self, key, values):
        for value in values:
            self.put(key, str(value))

    def putstring(self, key, value):
        self.put(key, value.encode('utf-8'))

    def putstrings(self, key, values):
        for value in values:
            self.put(key, value.encode('utf-8'))

    def finalize(self):
        pass


reader = Reader(file('dave.cdb'))

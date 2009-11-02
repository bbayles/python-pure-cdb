#!/usr/bin/env python2.5

'''
Manipulate DJB's Constant Databases. These are 2 level disk-based hash tables
that efficiently handle thousands of keys, while remaining space-efficient.

    http://cr.yp.to/cdb.html

Note the Reader class reads the entire CDB into memory. When using Writer,
consider using Python's hash() instead of djb_hash() for a tidy speedup,
however readers must be similarly configured.
'''

from _struct import Struct
from itertools import chain


def py_djb_hash(s):
    '''Return the value of DJB's hash function for the given 8-bit string.'''
    h = 5381
    for c in s:
        h = (((h << 5) + h) ^ ord(c)) & 0xffffffff
    return h # for small strings, masking here is faster.

try:
    from _cdblib import djb_hash
except ImportError:
    djb_hash = py_djb_hash

read_2_le4 = Struct('<LL').unpack
write_2_le4 = Struct('<LL').pack


class Reader(object):
    '''A dictionary-like object for reading data stored in a Constant
    Database.'''

    def __init__(self, data, hashfn=djb_hash):
        '''Create an instance using the given string-like sequence, optionally
        specifying a non-default hash function.'''
        if len(data) < 2048:
            raise IOError('CDB too small')

        self.data = data
        self.hashfn = hashfn

        self.index = [read_2_le4(data[i:i+8]) for i in xrange(0, 2048, 8)]
        self.table_start = min(p[0] for p in self.index)
        # Assume load load factor is 0.5 like official CDB.
        self.length = sum(p[1] >> 1 for p in self.index)

    def iteritems(self):
        '''Like dict.iteritems(). Items are returned in insertion order.'''
        pos = 2048
        while pos < self.table_start:
            klen, dlen = read_2_le4(self.data[pos:pos+8])
            pos += 8

            key = self.data[pos:pos+klen]
            pos += klen

            data = self.data[pos:pos+dlen]
            pos += dlen

            yield key, data

    def items(self):
        '''Like dict.items().'''
        return list(self.iteritems())

    def iterkeys(self):
        '''Like dict.iterkeys().'''
        return (p[0] for p in self.iteritems())
    __iter__ = iterkeys

    def itervalues(self):
        '''Like dict.itervalues().'''
        return (p[1] for p in self.iteritems())

    def keys(self):
        '''Like dict.keys().'''
        return [p[0] for p in self.iteritems()]

    def values(self):
        '''Like dict.values().'''
        return [p[1] for p in self.iteritems()]

    def __getitem__(self, key):
        '''Like dict.__getitem__().'''
        value = self.get(key)
        if value is None:
            raise KeyError(key)
        return value

    def has_key(self, k):
        '''Return True if the given key exists in the database.'''
        return self.get(k) is not None
    __contains__ = has_key

    def __len__(self):
        '''Return the number of records in the database.'''
        return self.length

    def gets(self, key):
        '''Yield all values for the given key in the database, in the order in
        which they were inserted.'''
        # Truncate to 32 bits and remove sign.
        h = self.hashfn(key) & 0xffffffff
        start, nslots = self.index[h & 255]

        if nslots:
            end = start + (nslots << 3)
            slot_off = start + (((h >> 8) % nslots) << 3)

            for pos in chain(xrange(slot_off, end, 8),
                             xrange(start, slot_off, 8)):
                rec_h, rec_pos = read_2_le4(self.data[pos:pos+8])

                if not rec_h:
                    break
                elif rec_h == h:
                    klen, dlen = read_2_le4(self.data[rec_pos:rec_pos+8])
                    rec_pos += 8

                    if self.data[rec_pos:rec_pos+klen] == key:
                        rec_pos += klen
                        yield self.data[rec_pos:rec_pos+dlen]

    def get(self, key, default=None):
        '''Return the first value for the given key in the database, or if it
        doesn't exist, return None or the given default.'''
        # Avoid exception catch when handling default case; much faster.
        return chain(self.gets(key), (default,)).next()

    def getint(self, key, default=None, base=0):
        '''Return the first value for the given key converted to an integer, or
        if it doesn't exist, return None or the given default.'''
        value = self.get(key, default)
        if value is not default:
            return int(value, base)
        return value

    def getints(self, key, base=0):
        '''Yield all values for the given key in the database, in the order in
        which they were inserted, after converting them to integers.'''
        return (int(v, base) for v in self.gets(key))

    def getstring(self, key, default=None, encoding='utf-8'):
        '''Return the first value for the given key decoded as a UTF-8 string
        or the encoding specified, or if it doesn't exist, return None or the
        given default.'''
        value = self.get(key, default)
        if value is not default:
            return value.decode(encoding)
        return value

    def getstrings(self, key, encoding='utf-8'):
        '''Yield all values for the given key in the database, in the order in
        which they were inserted, after decoding them as UTF-8 strings, or the
        encoding specified.'''
        return (v.decode(encoding) for v in self.gets(key))


class Writer(object):
    '''Object for building new Constant Databases, and writing them to a
    seekable file-like object.'''

    def __init__(self, fp, hashfn=djb_hash):
        '''Initialize a new instance that writes to the given file-like object
        using the given hash function, or DJB's function if unspecified.'''
        self.fp = fp
        self.hashfn = hashfn

        fp.write('\x00' * 2048)
        self._unordered = [[] for i in xrange(256)]

    def put(self, key, value=''):
        '''Write a string key/value pair to the output file.'''
        assert type(key) is str and type(value) is str

        pos = self.fp.tell()
        self.fp.write(write_2_le4(len(key), len(value)))
        self.fp.write(key)
        self.fp.write(value)

        h = self.hashfn(key) & 0xffffffff
        self._unordered[h & 0xff].append((h, pos))

    def puts(self, key, values):
        '''Write more than one value for the same key to the output file.
        Equivalent to calling put() in a loop.'''
        for value in values:
            self.put(key, value)

    def putint(self, key, value):
        '''Write an integer as a base-10 string associated with the given key
        to the output file.'''
        self.put(key, str(value))

    def putints(self, key, values):
        '''Write zero or more integers for the same key to the output file.
        Equivalent to calling putint() in a loop.'''
        self.puts(key, (str(value) for value in values))

    def putstring(self, key, value, encoding='utf-8'):
        '''Write a unicode string associated with the given key to the output
        file after encoding it as UTF-8 or the given encoding.'''
        self.put(key, unicode.encode(value, encoding))

    def putstrings(self, key, values, encoding='utf-8'):
        '''Write zero or more unicode strings to the output file. Equivalent to
        calling putstring() in a loop.'''
        self.puts(key, (unicode.encode(value, encoding) for value in values))

    def finalize(self):
        '''Write the final hash tables to the output file, and write out its
        index. The output file remains open upon return.'''
        index = []
        for tbl in self._unordered:
            length = len(tbl) << 1
            ordered = [(0, 0)] * length
            for pair in tbl:
                where = (pair[0] >> 8) % length
                for i in chain(xrange(where, length), xrange(0, where)):
                    if not ordered[i][0]:
                        ordered[i] = pair
                        break

            index.append((self.fp.tell(), length))
            for pair in ordered:
                self.fp.write(write_2_le4(*pair))

        self.fp.seek(0)
        for pair in index:
            self.fp.write(write_2_le4(*pair))
        self.fp = None # prevent double finalize()

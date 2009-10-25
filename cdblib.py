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


UNSPECIFIED = [None]

def djb_hash(s):
    '''Return the value of DJB's hash function for the given 8-bit string.'''
    h = 5381
    for c in s:
        h = (((h << 5) + h) ^ ord(c)) & 0xffffffff
    return h # for small strings, masking here is faster.

read_2_le4 = Struct('<LL').unpack
write_2_le4 = Struct('<LL').pack


class Reader(object):
    '''A dictionary-like object for reading data stored in a Constant
    Database.'''

    __slots__ = ('data', 'table_start', 'length', 'hash')

    def __init__(self, fp, hash=djb_hash):
        '''Initialize a new instance by reading the CDB from the given
        file-like object into memory, optionally specifying a non-default hash
        function (e.g. __builtin__.hash).'''
        self.data = fp.read()
        if len(self.data) < 2048:
            raise IOError('CDB too small')

        self.hash = hash
        self.table_start = None
        self.length = None

    def _get_value(self, pos, key):
        '''Decode the item record stored at the given position, verify its key
        matches the given key, and return its value part on match, otherwise
        return None.'''
        klen, dlen = read_2_le4(self.data[pos:pos+8])
        pos += 8

        if self.data[pos:pos+klen] == key:
            pos += klen
            return self.data[pos:pos+dlen]

    def iteritems(self):
        '''Like dict.iteritems(). Items are returned in insertion order.'''
        if self.table_start is None:
            self.table_start = min(read_2_le4(self.data[i:i+8])[0]
                                   for i in range(0, 2048, 8))

        pos = 2048
        while pos < self.table_start:
            klen, dlen = read_2_le4(self.data[pos:pos+8])
            pos += 8

            key = self.data[pos:pos+klen]
            pos += klen

            data = self.data[pos:pos+dlen]
            pos += dlen

            yield key, data

    def iterkeys(self):
        '''Like dict.iterkeys().'''
        return (p[0] for p in self.iteritems())
    __iter__ = iterkeys

    def itervalues(self):
        '''Like dict.itervalues().'''
        return (p[1] for p in self.iteritems())

    def keys(self):
        '''Like dict.keys().'''
        return list(p[0] for p in self.iteritems())

    def values(self):
        '''Like dict.values().'''
        return list(p[1] for p in self.iteritems())

    def has_key(self, k):
        '''Return True if the given key exists in the database.'''
        return self.get(k, None) is not None
    __contains__ = has_key

    def __len__(self):
        '''Return the number of records in the database.'''
        if self.length is None:
            # TODO(dmw): can't really rely on load factor being 0.5
            self.length = sum(read_2_le4(self.data[i:i+8])[1] / 2
                              for i in range(0, 2048, 8))
        return self.length

    def gets(self, key):
        '''Yield all values for the given key in the database, in the order in
        which they were inserted.'''
        # Truncate to 32 bits and remove sign.
        h = self.hash(key) & 0xffffffff
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
        '''Return the first value for the given key in the database, raising
        KeyError if it does not exist, or returning a default value if
        specified.'''
        if default is UNSPECIFIED:
            try:
                return self.gets(key).next()
            except StopIteration:
                raise KeyError(key)

        # Avoid exception catch when handling default case; much faster.
        return chain(self.gets(key), (default,)).next()
    __getitem__ = get

    def getint(self, key, default=UNSPECIFIED, base=0):
        '''Return the first value for the given key converted to an integer,
        raising KeyError if it does not exist, or returning a default value if
        specified.'''
        value = self.get(key, None)
        if value is None:
            if default is UNSPECIFIED:
                raise KeyError(key)
            return default
        return int(value, base)

    def getints(self, key, base=0):
        '''Yield all values for the given key in the database, in the order in
        which they were inserted, after converting them to integers.'''
        return (int(v, base) for v in self.gets(key))

    def getstring(self, key, default=UNSPECIFIED, encoding='utf-8'):
        '''Return the first value for the given key decoded as a UTF-8 string
        or the encoding specified, raising KeyError if it does not exist, or
        returning a default value if specified.'''
        value = self.get(key, None)
        if value is None:
            if default is UNSPECIFIED:
                raise KeyError(key)
            return default
        return value.decode(encoding)

    def getstrings(self, key, encoding='utf-8'):
        '''Yield all values for the given key in the database, in the order in
        which they were inserted, after decoding them as UTF-8 strings, or the
        encoding specified.'''
        return (v.decode(encoding) for v in self.gets(key))


class Writer(object):
    '''Object for building new Constant Databases, and writing them to a
    seekable file-like object.'''

    def __init__(self, fp, hash=djb_hash):
        '''Initialize a new instance that writes to the given file-like object
        using the given hash function, or DJB's function if unspecified.'''
        self.fp = fp
        self.hash = hash

        fp.write('\x00' * 2048)
        self._unordered = [[] for i in range(256)]

    def put(self, key, value):
        '''Write a string key/value pair to the output file.'''
        assert type(key) is str and type(value) is str

        pos = self.fp.tell()
        self.fp.write(write_2_le4(len(key), len(value)))
        self.fp.write(key)
        self.fp.write(value)

        h = self.hash(key) & 0xffffffff
        self._unordered[h & 0xff].append((h, pos))

    def puts(self, key, values):
        '''Write more than one value for the same key to the output file.
        Equivalent to calling put() in a loop.'''
        for value in values:
            self.put(key, value)

    def putkey(self, key):
        '''Write a key with a 0-length value to the output file.'''
        self.put(key, '')

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
        self.put(key, value.encode(encoding))

    def putstrings(self, key, values, encoding='utf-8'):
        '''Write zero or more unicode strings to the output file. Equivalent to
        calling putstring() in a loop.'''
        self.puts(key, (value.encode(encoding) for value in values))

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

'''
Manipulate DJB's Constant Databases. These are 2 level disk-based hash tables
that efficiently handle many keys, while remaining space-efficient.

    http://cr.yp.to/cdb.html

'''
from __future__ import unicode_literals

from struct import Struct
from itertools import chain

import six
from six.moves import range

from .djb_hash import djb_hash

# Structs for 32-bit databases
read_2_le4 = Struct('<LL').unpack
read_2_le8 = Struct('<QQ').unpack

# Structs for 64-bit databases
write_2_le4 = Struct('<LL').pack
write_2_le8 = Struct('<QQ').pack

# Encoders for keys
DEFAULT_ENCODERS = {six.text_type: lambda x: x.encode('utf-8')}
for t in six.integer_types:
    DEFAULT_ENCODERS[t] = lambda x: six.text_type(x).encode('utf-8')


class _CDBBase(object):
    def __init__(self, hashfn=djb_hash, strict=False, encoders=None):
        self.hashfn = hashfn

        if strict:
            self.hash_key = self.hash_key_strict

        self.encoders = DEFAULT_ENCODERS.copy()
        if encoders is not None:
            self.encoders.update(encoders)

    def hash_key(self, key):
        if not isinstance(key, six.binary_type):
            try:
                encoded_key = self.encoders[type(key)](key)
            except KeyError as e:
                e.args = 'could not encode {} to bytes'.format(key)
                raise
        else:
            encoded_key = key

        # Truncate to 32 bits and remove sign.
        h = self.hashfn(encoded_key)
        return encoded_key, (h & 0xffffffff)

    def hash_key_strict(self, key):
        try:
            h = self.hashfn(key)
        except TypeError as e:
            msg = 'key must be of type {}'
            e.args = (msg.format(six.binary_type.__name__),)
            raise

        # Truncate to 32 bits and remove sign.
        return key, (h & 0xffffffff)


class Reader(_CDBBase):
    '''A dictionary-like object for reading a Constant Database accessed
    through a string or string-like sequence, such as mmap.mmap().'''

    read_pair = staticmethod(read_2_le4)
    pair_size = 8

    def __init__(self, data, **kwargs):
        '''Create an instance reading from a sequence and using hashfn to hash
        keys.'''
        if len(data) < 2048:
            raise IOError('CDB too small')

        self.data = data
        self.index = [self.read_pair(data[i:i+self.pair_size])
                      for i in range(0, 256*self.pair_size, self.pair_size)]
        self.table_start = min(p[0] for p in self.index)
        # Assume load load factor is 0.5 like official CDB.
        self.length = sum(p[1] >> 1 for p in self.index)

        super(Reader, self).__init__(**kwargs)

    def iteritems(self):
        '''Like dict.iteritems(). Items are returned in insertion order.'''
        pos = self.pair_size * 256
        while pos < self.table_start:
            klen, dlen = self.read_pair(self.data[pos:pos+self.pair_size])
            pos += self.pair_size

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

    def has_key(self, key):
        '''Return True if key exists in the database.'''
        return self.get(key) is not None
    __contains__ = has_key

    def __len__(self):
        '''Return the number of records in the database.'''
        return self.length

    def gets(self, key):
        '''Yield values for key in insertion order.'''
        key, h = self.hash_key(key)
        start, nslots = self.index[h & 0xff]

        if nslots:
            end = start + (nslots * self.pair_size)
            slot_off = start + (((h >> 8) % nslots) * self.pair_size)

            for pos in chain(range(slot_off, end, self.pair_size),
                             range(start, slot_off, self.pair_size)):
                rec_h, rec_pos = self.read_pair(
                    self.data[pos:pos+self.pair_size]
                )

                if not rec_h:
                    break
                elif rec_h == h:
                    klen, dlen = self.read_pair(
                        self.data[rec_pos:rec_pos+self.pair_size]
                    )
                    rec_pos += self.pair_size

                    if self.data[rec_pos:rec_pos+klen] == key:
                        rec_pos += klen
                        yield self.data[rec_pos:rec_pos+dlen]

    def get(self, key, default=None):
        '''Get the first value for key, returning default if missing.'''
        # Avoid exception catch when handling default case; much faster.
        return next(chain(self.gets(key), (default,)))

    def getint(self, key, default=None, base=0):
        '''Get the first value for key converted it to an int, returning
        default if missing.'''
        value = self.get(key, default)
        if value is not default:
            return int(value, base)
        return value

    def getints(self, key, base=0):
        '''Yield values for key in insertion order after converting to int.'''
        return (int(v, base) for v in self.gets(key))

    def getstring(self, key, default=None, encoding='utf-8'):
        '''Get the first value for key decoded as unicode, returning default if
        not found.'''
        value = self.get(key, default)
        if value is not default:
            return value.decode(encoding)
        return value

    def getstrings(self, key, encoding='utf-8'):
        '''Yield values for key in insertion order after decoding as
        unicode.'''
        return (v.decode(encoding) for v in self.gets(key))


class Reader64(Reader):
    '''A cdblib.Reader variant to support reading from CDB files that use
    64-bit file offsets. The CDB file must be generated with an appropriate
    writer.'''

    read_pair = staticmethod(read_2_le8)
    pair_size = 16


class Writer(_CDBBase):
    '''Object for building new Constant Databases, and writing them to a
    seekable file-like object.'''

    write_pair = staticmethod(write_2_le4)
    pair_size = 8

    def __init__(self, fp, **kwargs):
        '''Create an instance writing to a file-like object, using hashfn to
        hash keys.'''
        self.fp = fp
        fp.write(b'\x00' * (256 * self.pair_size))
        self._unordered = [[] for i in range(256)]

        super(Writer, self).__init__(**kwargs)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.finalize()

    def put(self, key, value=b''):
        '''Write a string key/value pair to the output file.'''
        # Ensure that the value is binary
        if not isinstance(value, six.binary_type):
            msg = 'value must be of type {}'
            raise TypeError(msg.format(six.binary_type.__name__))

        # Computing the hash for the key also ensures that it's binary
        key, h = self.hash_key(key)

        pos = self.fp.tell()
        self.fp.write(self.write_pair(len(key), len(value)))
        self.fp.write(key)
        self.fp.write(value)

        self._unordered[h & 0xff].append((h, pos))

    def puts(self, key, values):
        '''Write more than one value for the same key to the output file.
        Equivalent to calling put() in a loop.'''
        for value in values:
            self.put(key, value)

    def putint(self, key, value):
        '''Write an integer as a base-10 string associated with the given key
        to the output file.'''
        self.put(key, str(int(value)).encode('ascii'))

    def putints(self, key, values):
        '''Write zero or more integers for the same key to the output file.
        Equivalent to calling putint() in a loop.'''
        self.puts(key, (str(int(value)).encode('ascii') for value in values))

    def putstring(self, key, value, encoding='utf-8'):
        '''Write a unicode string associated with the given key to the output
        file after encoding it as UTF-8 or the given encoding.'''
        self.put(key, six.text_type.encode(value, encoding))

    def putstrings(self, key, values, encoding='utf-8'):
        '''Write zero or more unicode strings to the output file. Equivalent to
        calling putstring() in a loop.'''
        self.puts(key, (six.text_type.encode(v, encoding) for v in values))

    def finalize(self):
        '''Write the final hash tables to the output file, and write out its
        index. The output file remains open upon return.'''
        index = []
        for tbl in self._unordered:
            length = len(tbl) * 2
            ordered = [(0, 0)] * length
            for pair in tbl:
                where = (pair[0] >> 8) % length
                for i in chain(range(where, length), range(0, where)):
                    if not ordered[i][0]:
                        ordered[i] = pair
                        break

            index.append((self.fp.tell(), length))
            for pair in ordered:
                self.fp.write(self.write_pair(*pair))

        self.fp.seek(0)
        for pair in index:
            self.fp.write(self.write_pair(*pair))
        self.fp = None  # prevent double finalize()


class Writer64(Writer):
    '''A cdblib.Writer variant to support writing CDB files that use 64-bit
    file offsets.'''

    write_pair = staticmethod(write_2_le8)
    pair_size = 16

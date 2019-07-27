'''
Manipulate DJB's Constant Databases. These are 2 level disk-based hash tables
that efficiently handle many keys, while remaining space-efficient.

    http://cr.yp.to/cdb.html

'''
from io import BytesIO
from os.path import isfile
from struct import Struct
from itertools import chain

from .djb_hash import djb_hash

# Structs for 32-bit databases
struct_32 = Struct('<LL')
read_2_le4 = struct_32.unpack
write_2_le4 = struct_32.pack

# Structs for 64-bit databases
struct_64 = Struct('<QQ')
read_2_le8 = struct_64.unpack
write_2_le8 = struct_64.pack

# Encoders for keys
DEFAULT_ENCODERS = {
    str: lambda x: x.encode('utf-8'),
    int: lambda x: str(x).encode('utf-8'),
}


def is_file(data):
    try:
        return isfile(data)
    except ValueError:
        return False


class _CDBBase(object):
    def __init__(self, hashfn=djb_hash, strict=False, encoders=None):
        self.hashfn = hashfn

        if strict:
            self.hash_key = self.hash_key_strict

        self.encoders = DEFAULT_ENCODERS.copy()
        if encoders is not None:
            self.encoders.update(encoders)

    def hash_key(self, key):
        if not isinstance(key, bytes):
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
            msg = 'key must be of type bytes'
            e.args = (msg,)
            raise

        # Truncate to 32 bits and remove sign.
        return key, (h & 0xffffffff)


class Reader(_CDBBase):
    unpack = struct_32.unpack
    read_size = struct_32.size

    def __init__(self, *args, **kwargs):
        # If one argument is given, treat it like a string of bytes.
        if len(args) == 1:
            self._init_data(args[0])
        # If keyword arguments are given, use them instead.
        elif len(args) == 0:
            if 'file_obj' in kwargs:
                self._file_obj = kwargs['file_obj']
            elif 'file_path' in kwargs:
                self._file_obj = open(kwargs['file_path'], 'rb')
            elif 'data' in kwargs:
                self._init_data(kwargs['data'])
            else:
                raise TypeError('No source data given')
        # Unknown input
        else:
            raise TypeError('Wrong number of arguments')

        self._read_pair = (
            lambda: self.unpack(self._file_obj.read(self.read_size))
        )
        self.pointers = [self._read_pair() for __ in range(256)]
        self.length = sum(p[1] for p in self.pointers) // 2

        super().__init__(**kwargs)

    def _init_data(self, data):
        if len(data) < (self.read_size * 256):
            raise IOError('CDB too small')

        self._file_obj = BytesIO(data)

    def __del__(self):
        self.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.close()

    def __iter__(self):
        return self.iterkeys()

    def __getitem__(self, key):
        value = self.get(key)
        if value is None:
            raise KeyError(key)
        return value

    def __len__(self):
        return self.length

    def close(self):
        try:
            self._file_obj.close()
        except Exception:
            pass

    def get(self, key, default=None):
        return next(self.gets(key), default)

    def getint(self, key, default=None, base=0):
        value = self.get(key, default)
        if value is not default:
            return int(value, base)
        return value

    def getints(self, key, base=0):
        return (int(v, base) for v in self.gets(key))

    def getstring(self, key, default=None, encoding='utf-8'):
        value = self.get(key, default)
        if value is not default:
            return value.decode(encoding)
        return value

    def getstrings(self, key, encoding='utf-8'):
        return (v.decode(encoding) for v in self.gets(key))

    def gets(self, key):
        key, hashed_key = self.hash_key(key)
        slot_number, table_number = divmod(hashed_key, 256)
        table_pos, table_len = self.pointers[table_number]
        if not table_len:
            return
        table_end = table_pos + (self.read_size * table_len)

        slot_number %= table_len
        slot_pos = table_pos + (self.read_size * slot_number)

        self._file_obj.seek(slot_pos)
        hash_value, byte_position = self._read_pair()
        check_positions = []
        while True:
            if (hash_value == hashed_key) and byte_position:
                check_positions.append(byte_position)
            if self._file_obj.tell() == table_end:
                self._file_obj.seek(table_pos)
            hash_value, byte_position = self._read_pair()
            if byte_position == 0:
                break

        for byte_position in check_positions:
            self._file_obj.seek(byte_position)
            key_size, value_size = self._read_pair()
            candidate_key = self._file_obj.read(key_size)
            candidate_value = self._file_obj.read(value_size)
            if candidate_key == key:
                yield candidate_value

    def has_key(self, key):
        return self.get(key) is not None

    __contains__ = has_key

    def iteritems(self):
        self._file_obj.seek(256 * self.read_size)
        for i in range(self.length):
            key_size, value_size = self._read_pair()
            key = self._file_obj.read(key_size)
            value = self._file_obj.read(value_size)
            yield key, value

    def iterkeys(self):
        return (k for k, v in self.iteritems())

    def itervalues(self):
        return (v for k, v in self.iteritems())

    def items(self):
        return list(self.iteritems())

    def keys(self):
        return list(self.iterkeys())

    def values(self):
        return list(self.itervalues())


class Reader64(Reader):
    '''A cdblib.Reader variant to support reading from CDB files that use
    64-bit file offsets. The CDB file must be generated with an appropriate
    writer.'''

    unpack = struct_64.unpack
    read_size = struct_64.size


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
        if not isinstance(value, bytes):
            raise TypeError('value must be of type bytes')

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
        self.put(key, value.encode(encoding))

    def putstrings(self, key, values, encoding='utf-8'):
        '''Write zero or more unicode strings to the output file. Equivalent to
        calling putstring() in a loop.'''
        self.puts(key, (v.encode(encoding) for v in values))

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

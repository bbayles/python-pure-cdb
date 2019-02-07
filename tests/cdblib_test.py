#!/usr/bin/env python
import hashlib
import io
import unittest

from functools import partial
from os.path import abspath, dirname, join
from struct import pack
from zlib import adler32

import cdblib


def testdata_path(file_name):
    return join(dirname(abspath(__file__)), 'testdata', file_name)


class DjbHashTestCase(unittest.TestCase):
    def test_known_good(self):
        self.assertEqual(cdblib.djb_hash(b'dave'), 2087378131)

    def test_correct_wrapping(self):
        h = cdblib.djb_hash(b'davedavedavedavedave')
        self.assertEqual(h, 3529598163)


class ReaderKnownGoodTestCase(unittest.TestCase):
    reader_cls = cdblib.Reader
    pwdump_path = testdata_path('pwdump.cdb')
    pwdump_md5 = '84d38c5b6b5bb01bb374b2f7af0129b1'
    top250_path = testdata_path('top250pws.cdb')
    top250_md5 = '0564adfe4667506a326ba2f363415616'

    def reader_to_cdbmake_md5(self, filename):
        md5 = hashlib.md5()

        with io.open(filename, 'rb') as infile:
            data = infile.read()

        for key, value in self.reader_cls(data).iteritems():
            # Hack to work around lack of bytes.format() in Python 3.4
            data = '+{},{}:{}->{}\n'.format(
                len(key),
                len(value),
                key.decode('utf-8'),
                value.decode('utf-8')
            )
            md5.update(data.encode('utf-8'))

        md5.update(b'\n')

        return md5.hexdigest()

    def test_read_pwdump(self):
        # MD5s here are of the source .cdbmake file.
        self.assertEqual(self.reader_to_cdbmake_md5(self.pwdump_path),
                         self.pwdump_md5)
        self.assertEqual(self.reader_to_cdbmake_md5(self.top250_path),
                         self.top250_md5)


class Reader64KnownGoodTestCase(ReaderKnownGoodTestCase):
    reader_cls = cdblib.Reader64
    pwdump_path = testdata_path('pwdump.cdb64')
    top250_path = testdata_path('top250pws.cdb64')


class ReaderDictLikeTestCase(unittest.TestCase):
    reader_cls = cdblib.Reader
    data_path = testdata_path('top250pws.cdb')

    def setUp(self):
        with io.open(self.data_path, 'rb') as infile:
            data = infile.read()

        self.reader = self.reader_cls(data)

    def test_iteritems(self):
        uniq_keys = set()
        uniq_values = set()
        for key, value in self.reader.iteritems():
            uniq_keys.add(key)
            uniq_values.add(value)

        self.assertEqual(len(uniq_keys), 250)
        self.assertEqual(len(uniq_values), 250)
        for key in uniq_keys:
            self.assertTrue(self.reader[key] in uniq_values)

    def test_items(self):
        for idx, (key, value) in enumerate(self.reader.items()):
            self.assertEqual(self.reader[key], value)
        self.assertEqual(idx, 249)

    def test_iterkeys(self):
        for key in self.reader.iterkeys():
            self.assertIs(type(self.reader[key]), bytes)

    def test___iter__(self):
        for key in self.reader:
            self.assertIs(type(self.reader[key]), bytes)

    def test_values_itervalues(self):
        inverted = dict((v, k) for (k, v) in self.reader.iteritems())
        for value in self.reader.itervalues():
            self.assertIn(value, inverted)
            self.assertEqual(self.reader[inverted[value]], value)

    def test_keys(self):
        self.assertEqual(self.reader.keys(), list(self.reader.iterkeys()))

    def test_values(self):
        self.assertEqual(self.reader.values(), list(self.reader.itervalues()))

    def test_has_key_contains(self):
        for key in self.reader:
            self.assertTrue(self.reader.has_key(key))
            self.assertIn(key, self.reader)

        for key in (b'zarg zarg warf!', b'doesnt exist really'):
            self.assertFalse(self.reader.has_key(key))
            self.assertNotIn(key, self.reader)
            # there's no __notcontains__, right?
            self.assertTrue(key not in self.reader)

    def test_len(self):
        self.assertEqual(len(self.reader), 250)
        self.assertEqual(len(list(self.reader)), 250)

    def test_get_no_default(self):
        get = self.reader.get

        self.assertEqual(get(b'123456'), b'1')
        self.assertEqual(get(b'love'), b'12')
        self.assertEqual(get(b'!!KinDaCompleX'), None)
        self.assertEqual(get(b'^^Hashes_Differently'), None)

    def test_get_default(self):
        get = self.reader.get

        self.assertEqual(get(b'123456', b'default'), b'1')
        self.assertEqual(get(b'love', b'default'), b'12')
        self.assertEqual(get(b'!!KinDaCompleX', b'default'), b'default')
        self.assertEqual(get(b'^^Hashes_Differently', b'default'), b'default')


class Reader64DictLikeTestCase(ReaderDictLikeTestCase):
    reader_cls = cdblib.Reader64
    data_path = testdata_path('top250pws.cdb64')


class ReaderNativeInterfaceTestBase(object):
    ARTS = (u'\N{SNOWMAN}', u'\N{CLOUD}', u'\N{UMBRELLA}')
    reader_cls = cdblib.Reader
    writer_cls = cdblib.Writer

    def setUp(self):
        self.sio = sio = io.BytesIO()
        writer = self.writer_cls(sio, hashfn=self.HASHFN)
        writer.puts(b'dave', [str(i).encode('ascii') for i in range(10)])
        writer.put(b'dave_no_dups', b'1')
        writer.put(b'dave_hex', b'0x1a')
        writer.putstrings(b'art', self.ARTS)
        writer.finalize()

        sio.seek(0)
        self.reader = self.reader_cls(sio.getvalue(), hashfn=self.HASHFN)

    def test_insertion_order(self):
        keys  = [b'dave'] * 10
        keys.append(b'dave_no_dups')
        keys.append(b'dave_hex')
        keys.extend(b'art' for art in self.ARTS)
        self.assertEqual(self.reader.keys(), keys)

    def test_get(self):
        # First get on a key should return its first inserted value.
        self.assertEqual(self.reader.get(b'dave'), b'0')
        self.assertEqual(self.reader.get(b'dave_no_dups'), b'1')

        # Default.
        self.assertEqual(self.reader.get(b'junk', b'wad'), b'wad')
        self.assertEqual(None, self.reader.get(b'junk'))

    def test__getitem__(self):
        self.assertEqual(self.reader[b'dave'], b'0')
        self.assertEqual(self.reader[b'dave_no_dups'], b'1')
        self.assertRaises(KeyError, lambda: self.reader[b'junk'])

    def test_gets(self):
        self.assertEqual(
            list(self.reader.gets(b'dave')),
            [str(i).encode('ascii') for i in range(10)],
        )
        self.assertEqual(
            list(self.reader.gets(b'dave_no_dups')),
            [b'1']
        )
        self.assertEqual(
            list(self.reader.gets(b'art')),
            [s.encode('utf-8') for s in self.ARTS ]
        )
        self.assertEqual(list(self.reader.gets(b'junk')), [])

    def test_getint(self):
        self.assertEqual(self.reader.getint(b'dave'), 0)
        self.assertEqual(self.reader.getint(b'dave_no_dups'), 1)
        self.assertEqual(self.reader.getint(b'dave_hex', 16), 26)
        self.assertRaises(ValueError, self.reader.getint, b'art')

        self.assertEqual(self.reader.get(b'junk', 1), 1)
        self.assertEqual(None, self.reader.getint(b'junk'))

    def test_getints(self):
        self.assertEqual(
            list(self.reader.getints(b'dave')),
            list(range(10))
        )
        self.assertRaises(ValueError, list, self.reader.getints(b'art'))

        self.assertEqual(list(self.reader.getints(b'junk')), [])

    def test_getstring(self):
        self.assertEqual(self.reader.getstring(b'art'), u'\N{SNOWMAN}')
        self.assertEqual(type(self.reader.getstring(b'art')), str)
        self.assertEqual(None, self.reader.getstring(b'junk'))

        self.assertEqual(
            self.reader.getstring(b'junk', u'\N{COMET}'),
            u'\N{COMET}'
        )

    def test_getstrings(self):
        art_strings = tuple(self.reader.getstrings(b'art'))
        self.assertEqual(art_strings, self.ARTS)
        self.assertTrue(
            all(type(s) is str for s in art_strings)
        )
        self.assertEqual(list(self.reader.getstrings(b'junk')), [])


class ReaderNativeInterfaceDjbHashTestCase(ReaderNativeInterfaceTestBase,
                                           unittest.TestCase):
    HASHFN = staticmethod(cdblib.djb_hash)


class Reader64NativeInterfaceDjbHashTestCase(ReaderNativeInterfaceTestBase,
                                             unittest.TestCase):
    reader_cls = cdblib.Reader64
    writer_cls = cdblib.Writer64
    HASHFN = staticmethod(cdblib.djb_hash)


class ReaderNativeInterfaceNullHashTestCase(ReaderNativeInterfaceTestBase,
                                            unittest.TestCase):
    # Ensure collisions don't result in the wrong keys being returned.
    HASHFN = staticmethod(lambda s: 1)


class Reader64NativeInterfaceNullHashTestCase(ReaderNativeInterfaceTestBase,
                                              unittest.TestCase):
    reader_cls = cdblib.Reader64
    writer_cls = cdblib.Writer64
    # Ensure collisions don't result in the wrong keys being returned.
    HASHFN = staticmethod(lambda s: 1)


class ReaderNativeInterfaceAltHashTestCase(ReaderNativeInterfaceTestBase,
                                           unittest.TestCase):
    # Use the adler32 checksum as a "hash"
    HASHFN = staticmethod(lambda s: adler32(s) & 0xffffffff)


class Reader64NativeInterfaceAltHashTestCase(ReaderNativeInterfaceTestBase,
                                             unittest.TestCase):
    reader_cls = cdblib.Reader64
    writer_cls = cdblib.Writer64
    # Use the adler32 checksum as a "hash"
    HASHFN = staticmethod(lambda s: adler32(s) & 0xffffffff)


class WriterNativeInterfaceTestBase(object):
    reader_cls = cdblib.Reader
    writer_cls = cdblib.Writer

    def setUp(self):
        self.sio = sio = io.BytesIO()
        self.writer = self.writer_cls(sio, hashfn=self.HASHFN, strict=True)

    def get_reader(self):
        self.writer.finalize()
        return self.reader_cls(
            self.sio.getvalue(), hashfn=self.HASHFN, strict=True
        )

    def test_put(self):
        self.writer.put(b'dave', b'dave')
        self.assertEqual(self.get_reader().get(b'dave'), b'dave')

    def test_put_fail(self):
        for key, value, exc_type in [
            # Key is not binary
            (u'dave', b'dave', TypeError),
            (123, b'dave', TypeError),
            # Value is not binary
            (b'dave', u'dave', TypeError),
            (b'dave', 123, TypeError),
        ]:
            with self.assertRaises(exc_type):
                self.writer.put(key, value)

    def test_puts(self):
        lst = b'dave dave dave'.split()
        self.writer.puts(b'dave', lst)
        self.assertEqual(list(self.get_reader().gets(b'dave')), lst)

    def test_puts_fail(self):
        lst = b'dave dave dave'.split()
        for key, value, exc_type in [
            # Key is not binary
            (u'dave', lst, TypeError),
            (123, lst, TypeError),
            # Value is not binary
            (b'dave', map(str, lst), TypeError),
            (b'dave', (123,), TypeError),
        ]:
            with self.assertRaises(exc_type):
                self.writer.puts(key, value)

    def test_putint(self):
        self.writer.putint(b'dave', 26)
        self.writer.putint(b'dave2', 26 << 32)
        self.writer.putint(b'dave3', True)  # int(True) is 1
        self.writer.putint(b'dave4', False)  # int(False) is 0

    def test_putint_fail(self):
        for key, value, exc_type in [
            # Key is not binary
            (u'dave', 123, TypeError),
            (123, 123, TypeError),
            # Value is not int
            (b'dave', b'', ValueError),
            (b'dave', u'', ValueError),
            (b'dave', None, TypeError),
        ]:
            with self.assertRaises(exc_type):
                self.writer.putint(key, value)

    def test_putints(self):
        self.writer.putints(b'dave', range(10))
        self.assertEqual(
            list(self.get_reader().getints(b'dave')),
            list(range(10))
        )

    def test_putints_fail(self):
        for key, value, exc_type in [
            # Key is not binary
            (u'dave', [123], TypeError),
            (123, [123], TypeError),
            # Value is not an iterable of ints
            (b'dave', [123, b''], ValueError),
            (b'dave', [123, u''], ValueError),
            (b'dave', [123, None], TypeError),
        ]:
            with self.assertRaises(exc_type):
                self.writer.putints(key, value)

    def test_putstring(self):
        self.writer.putstring(b'dave', u'dave')
        self.assertEqual(self.get_reader().getstring(b'dave'), u'dave')

    def test_putstring_fail(self):
        exc_types = (AttributeError, TypeError)
        for key, value, exc_type in [
            # Key is not binary
            (u'dave', u'dave', exc_types),
            (123, u'dave', exc_types),
            # Value is not a string
            (b'dave', 123, exc_types),
            (b'dave', True, exc_types),
            (b'dave', None, exc_types),
        ]:
            with self.assertRaises(exc_type):
                self.writer.putstring(key, value)

    def test_putstrings(self):
        lst = [u'zark', u'quark']
        self.writer.putstrings(b'dave', lst)
        self.assertEqual(list(self.get_reader().getstrings(b'dave')), lst)

    def test_putstrings_fail(self):
        exc_types = (AttributeError, TypeError)
        for key, value, exc_type in [
            # Key is not binary
            (u'dave', u'dave', exc_types),
            (123, u'dave', exc_types),
            # Value is not an iterable of strings
            (b'dave', [u'123', 123], exc_types),
            (b'dave', [u'123', True], exc_types),
            (b'dave', [u'123', None], exc_types),
        ]:
            with self.assertRaises(exc_type):
                self.writer.putstrings(key, value)


class WriterNativeInterfaceDjbHashTestCase(WriterNativeInterfaceTestBase,
                                           unittest.TestCase):
    HASHFN = staticmethod(cdblib.djb_hash)


class Writer64NativeInterfaceDjbHashTestCase(WriterNativeInterfaceTestBase,
                                             unittest.TestCase):
    reader_cls = cdblib.Reader64
    writer_cls = cdblib.Writer64
    HASHFN = staticmethod(cdblib.djb_hash)


class WriterNativeInterfaceNullHashTestCase(WriterNativeInterfaceTestBase,
                                            unittest.TestCase):
    HASHFN = staticmethod(lambda s: 1)


class WriterNativeInterfaceNullHashTestCase(WriterNativeInterfaceTestBase,
                                            unittest.TestCase):
    reader_cls = cdblib.Reader64
    writer_cls = cdblib.Writer64
    HASHFN = staticmethod(lambda s: 1)


class WriterNativeInterfaceAltHashTestCase(WriterNativeInterfaceTestBase,
                                           unittest.TestCase):
    HASHFN = staticmethod(lambda s: adler32(s) & 0xffffffff)


class WriterNativeInterfaceAltHashTestCase(WriterNativeInterfaceTestBase,
                                           unittest.TestCase):
    reader_cls = cdblib.Reader64
    writer_cls = cdblib.Writer64
    HASHFN = staticmethod(lambda s: adler32(s) & 0xffffffff)


class WriterKnownGoodTestBase(object):
    reader_cls = cdblib.Reader
    writer_cls = cdblib.Writer

    top250_path = testdata_path('top250pws.cdb')
    pwdump_path = testdata_path('pwdump.cdb')

    def setUp(self):
        self.sio = io.BytesIO()
        self.writer = self.writer_cls(
            self.sio, hashfn=self.HASHFN, strict=True
        )

    def get_md5(self):
        self.writer.finalize()
        return hashlib.md5(self.sio.getvalue()).hexdigest()

    def test_empty(self):
        self.assertEqual(self.get_md5(), self.EMPTY_MD5)

    def test_single_rec(self):
        self.writer.put(b'dave', b'dave')
        self.assertEqual(self.get_md5(), self.SINGLE_REC_MD5)

    def test_context_manager_recovery(self):
        # The context manager should finalize the file even if there's an error
        # while it's open
        with io.BytesIO() as f:
            with self.writer_cls(f, hashfn=self.HASHFN, strict=True) as writer:
                writer.put(b'dave', b'dave')
                self.assertRaises(Exception, lambda: self.writer.put, 1)

            self.assertEqual(
                hashlib.md5(f.getvalue()).hexdigest(), self.SINGLE_REC_MD5
            )

    def test_dup_keys(self):
        self.writer.puts(b'dave', (b'dave', b'dave'))
        self.assertEqual(self.get_md5(), self.DUP_KEYS_MD5)

    def get_iteritems(self, filename):
        with io.open(filename, 'rb') as infile:
            data = infile.read()

        reader = self.reader_cls(data, hashfn=self.HASHFN, strict=True)
        return reader.iteritems()

    def test_known_good_top250(self):
        for key, value in self.get_iteritems(self.top250_path):
            self.writer.put(key, value)
        self.assertEqual(self.get_md5(), self.TOP250PWS_MD5)

    def test_known_good_top250_context_manager(self):
        with io.BytesIO() as f:
            with self.writer_cls(f, hashfn=self.HASHFN, strict=True) as writer:
                for key, value in self.get_iteritems(self.top250_path):
                    writer.put(key, value)

            self.assertEqual(
                hashlib.md5(f.getvalue()).hexdigest(), self.TOP250PWS_MD5
            )

    def test_known_good_pwdump(self):
        for key, value in self.get_iteritems(self.pwdump_path):
            self.writer.put(key, value)
        self.assertEqual(self.get_md5(), self.PWDUMP_MD5)

    def test_known_good_pwdump_context_manager(self):
        with io.BytesIO() as f:
            with self.writer_cls(f, hashfn=self.HASHFN, strict=True) as writer:
                for key, value in self.get_iteritems(self.pwdump_path):
                    writer.put(key, value)

            self.assertEqual(
                hashlib.md5(f.getvalue()).hexdigest(), self.PWDUMP_MD5
            )


class WriterKnownGoodDjbHashTestCase(WriterKnownGoodTestBase,
                                     unittest.TestCase):
    HASHFN = staticmethod(cdblib.djb_hash)

    EMPTY_MD5 = 'a646d6b87720195feb973de130b10123'
    SINGLE_REC_MD5 = 'd94cdc896807d5b7ab5be0078d1469dc'
    DUP_KEYS_MD5 = 'cb67e9e167cefcaddf62f03baa7f6c72'
    TOP250PWS_MD5 = 'ebcba66c01a4ed61a777bd16cf07e1b1'
    PWDUMP_MD5 = '15993a395e1245af2a476601c219b3e5'


class Writer64KnownGoodDjbHashTestCase(WriterKnownGoodTestBase,
                                       unittest.TestCase):
    HASHFN = staticmethod(cdblib.djb_hash)
    reader_cls = cdblib.Reader64
    writer_cls = cdblib.Writer64
    top250_path = testdata_path('top250pws.cdb64')
    pwdump_path = testdata_path('pwdump.cdb64')

    EMPTY_MD5 = 'c43c406a037989703e0d58ed9f17ba3c'
    SINGLE_REC_MD5 = '276ae8223f730b1e67007641db6b69ca'
    DUP_KEYS_MD5 = '1aae63d751ce5eea9e61916ae0aa00b3'
    TOP250PWS_MD5 = 'c6bdb3c7645c5d62747ac74895f9e90a'
    PWDUMP_MD5 = '3b1b4964294897c6ca119a6c6ae0094f'


class WriterKnownGoodNullHashTestCase(WriterKnownGoodTestBase,
                                      unittest.TestCase):
    HASHFN = staticmethod(lambda s: 1)

    EMPTY_MD5 = 'a646d6b87720195feb973de130b10123'
    SINGLE_REC_MD5 = 'f8cc0cdd90fe45193f7d53980c354d5f'
    DUP_KEYS_MD5 = '3d5ad135593c942cf9621d3d4a1f6637'
    TOP250PWS_MD5 = '0a5fff8836a175460ead340afff2d301'
    PWDUMP_MD5 = 'eac33af35208c7daba0487d0d411b8d5'


class Writer64KnownGoodNullHashTestCase(WriterKnownGoodTestBase,
                                        unittest.TestCase):
    HASHFN = staticmethod(lambda s: 1)
    reader_cls = cdblib.Reader64
    writer_cls = cdblib.Writer64
    top250_path = testdata_path('top250pws.cdb64')
    pwdump_path = testdata_path('pwdump.cdb64')

    EMPTY_MD5 = 'c43c406a037989703e0d58ed9f17ba3c'
    SINGLE_REC_MD5 = '91f0614d6ec48e720138d6e962062166'
    DUP_KEYS_MD5 = 'e1fe0e8ae7bacd9dbe6a87cfccc627fa'
    TOP250PWS_MD5 = '25519af3e573e867f423956fc6e9b8e8'
    PWDUMP_MD5 = '5a8d1dd40d82af01cbb23ceab16c1588'


class StrictnessTestsBase(object):
    def test_string_keys(self):
        with io.BytesIO() as f:
            with self.writer_cls(f) as writer:
                writer.put(u'key_1', b'11')
                writer.puts(u'key_2', [b'21', b'22'])
                writer.putint(u'key_3', 31)
                writer.putints(u'key_4', [41, 42])
                writer.putstring(u'key_5', u's51')
                writer.putstrings(u'key_6', [u's61', u'62'])

            reader = self.reader_cls(f.getvalue(), strict=False)
            self.assertEqual(reader.get(u'key_1'), b'11')
            self.assertEqual(list(reader.gets(u'key_2')), [b'21', b'22'])
            self.assertEqual(reader.getint(u'key_3'), 31)
            self.assertEqual(list(reader.getints(u'key_4')), [41, 42])
            self.assertEqual(reader.getstring(u'key_5'), u's51')
            self.assertEqual(
                list(reader.getstrings(u'key_6')), [u's61', u'62']
            )

    def test_int_keys(self):
        with io.BytesIO() as f:
            with self.writer_cls(f) as writer:
                writer.put(1, b'11')
                writer.puts(2, [b'21', b'22'])
                writer.putint(3, 31)
                writer.putints(4, [41, 42])
                writer.putstring(5, u's51')
                writer.putstrings(6, [u's61', u'62'])

            reader = self.reader_cls(f.getvalue(), strict=False)

        self.assertEqual(reader.get(1), b'11')
        self.assertEqual(list(reader.gets(2)), [b'21', b'22'])
        self.assertEqual(reader.getint(3), 31)
        self.assertEqual(list(reader.getints(4)), [41, 42])
        self.assertEqual(reader.getstring(5), u's51')
        self.assertEqual(list(reader.getstrings(6)), [u's61', u'62'])

    def test_encoding(self):
        # b'1', u'1', and 1 all encode to the same thing, so writing to
        # one is the same as writing to all.
        with io.BytesIO() as f:
            with self.writer_cls(f) as writer:
                writer.put(1, b'11')
                writer.put(u'1', b'12')
                writer.put(b'1', b'13')

            reader = self.reader_cls(f.getvalue())

        self.assertEqual(list(reader.gets(1)), [b'11', b'12', b'13'])
        self.assertEqual(list(reader.gets(u'1')), [b'11', b'12', b'13'])
        self.assertEqual(list(reader.gets(b'1')), [b'11', b'12', b'13'])

    def test_custom_encoding(self):
        encoders = {
            # override int encoder
            int: lambda x: pack('!H', x),
            # add list encoder
            list: lambda x: b'|'.join(x)
        }
        with io.BytesIO() as f:
            with self.writer_cls(f, encoders=encoders) as writer:
                # Override in place - ints get encoded differently
                writer.put(257, b'\x01\x01')
                # New encoder - lists get encoded instead of throwing errors
                writer.put([b'key_1', b'key_2'], b'key_1|key_2')
                # No override; default encoder for string is active
                writer.put(u'\N{SNOWMAN}', b'\xe2\x98\x83')
                # No encoder for None - error
                with self.assertRaises(KeyError):
                    writer.put(None, b'fail!')

            reader = self.reader_cls(f.getvalue(), encoders=encoders)

        # Read back as non-binary types and as the corresponding binary type
        for key, value in [
            (257, b'\x01\x01'),
            ([b'key_1', b'key_2'], b'key_1|key_2'),
            (u'\N{SNOWMAN}', b'\xe2\x98\x83'),
        ]:
            self.assertEqual(reader.get(key), value)
            self.assertEqual(reader.get(value), value)

class StrictnessTests32(StrictnessTestsBase, unittest.TestCase):
    reader_cls = cdblib.Reader
    writer_cls = cdblib.Writer


class StrictnessTests64(StrictnessTestsBase, unittest.TestCase):
    reader_cls = cdblib.Reader64
    writer_cls = cdblib.Writer64


if __name__ == '__main__':
    unittest.main()

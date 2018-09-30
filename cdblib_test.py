#!/usr/bin/env python
from __future__ import unicode_literals

import hashlib
import io
import unittest

from functools import partial

import six

import cdblib


class DjbHashTestCase(unittest.TestCase):
    def test_known_good(self):
        self.assertEqual(cdblib.djb_hash(b'dave'), 2087378131)

    def test_correct_wrapping(self):
        h = cdblib.djb_hash(b'davedavedavedavedave')
        self.assertEqual(h, 3529598163)


class ReaderKnownGoodTestCase(unittest.TestCase):
    reader_cls = cdblib.Reader
    pwdump_path = 'testdata/pwdump.cdb'
    pwdump_md5 = '84d38c5b6b5bb01bb374b2f7af0129b1'
    top250_path = 'testdata/top250pws.cdb'
    top250_md5 = '0564adfe4667506a326ba2f363415616'

    def reader_to_cdbmake_md5(self, filename):
        md5 = hashlib.md5()

        with io.open(filename, 'rb') as infile:
            data = infile.read()

        for key, value in self.reader_cls(data).iteritems():
            md5.update(b'+%d,%d:%s->%s\n' % (len(key), len(value), key, value))

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
    pwdump_path = 'testdata/pwdump.cdb64'
    top250_path = 'testdata/top250pws.cdb64'


class ReaderDictLikeTestCase(unittest.TestCase):
    reader_cls = cdblib.Reader
    data_path = 'testdata/top250pws.cdb'

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
            self.assertIs(type(self.reader[key]), six.binary_type)

    def test___iter__(self):
        for key in self.reader:
            self.assertIs(type(self.reader[key]), six.binary_type)

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
    data_path = 'testdata/top250pws.cdb64'


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
        self.assertEqual(type(self.reader.getstring(b'art')), six.text_type)
        self.assertEqual(None, self.reader.getstring(b'junk'))

        self.assertEqual(
            self.reader.getstring(b'junk', u'\N{COMET}'),
            u'\N{COMET}'
        )

    def test_getstrings(self):
        art_strings = tuple(self.reader.getstrings(b'art'))
        self.assertEqual(art_strings, self.ARTS)
        self.assertTrue(
            all(type(s) is six.text_type for s in art_strings)
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


class ReaderNativeInterfaceNativeHashTestCase(ReaderNativeInterfaceTestBase,
                                              unittest.TestCase):
    HASHFN = staticmethod(hash)


class Reader64NativeInterfaceNativeHashTestCase(ReaderNativeInterfaceTestBase,
                                                unittest.TestCase):
    reader_cls = cdblib.Reader64
    writer_cls = cdblib.Writer64
    HASHFN = staticmethod(hash)


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


class WriterNativeInterfaceTestBase(object):
    reader_cls = cdblib.Reader
    writer_cls = cdblib.Writer

    def setUp(self):
        self.sio = sio = io.BytesIO()
        self.writer = self.writer_cls(sio, hashfn=self.HASHFN)

    def get_reader(self):
        self.writer.finalize()
        return self.reader_cls(self.sio.getvalue(), hashfn=self.HASHFN)

    def make_bad(self, method):
        return partial(self.assertRaises, Exception, method)

    def test_put(self):
        self.writer.put(b'dave', b'dave')
        self.assertEqual(self.get_reader().get(b'dave'), b'dave')

        # Don't care about rich error, just as long as it crashes.
        bad = self.make_bad(self.writer.put)
        bad(b'dave', u'dave')
        bad(u'dave', b'dave')
        bad(b'dave', 123)
        bad(123, b'dave')

    def test_puts(self):
        lst = b'dave dave dave'.split()

        self.writer.puts(b'dave', lst)
        self.assertEqual(list(self.get_reader().gets(b'dave')), lst)

        bad = self.make_bad(self.writer.puts)
        bad('dave', map(six.text_type, lst))
        bad(u'dave', lst)
        bad(b'dave', (123,))
        bad(123, lst)

    def test_putint(self):
        self.writer.putint(b'dave', 26)
        self.writer.putint(b'dave2', 26 << 32)

        reader = self.get_reader()
        self.assertEqual(reader.getint(b'dave'), 26)
        self.assertEqual(reader.getint(b'dave2'), 26 << 32)

        bad = self.make_bad(self.writer.putint)
        bad(True)
        bad(b'dave')
        bad(None)

    def test_putints(self):
        self.writer.putints(b'dave', range(10))
        self.assertEqual(
            list(self.get_reader().getints(b'dave')),
            list(range(10))
        )

        bad = self.make_bad(self.writer.putints)
        bad((True, False))
        bad(b'dave')
        bad(u'dave')

    def test_putstring(self):
        self.writer.putstring(b'dave', u'dave')
        self.assertEqual(self.get_reader().getstring(b'dave'), u'dave')

        bad = self.make_bad(self.writer.putstring)
        bad(b'dave')
        bad(123)
        bad(None)

    def test_putstrings(self):
        lst = [u'zark', u'quark']
        self.writer.putstrings(b'dave', lst)
        self.assertEqual(list(self.get_reader().getstrings(b'dave')), lst)

        bad = self.make_bad(self.writer.putstrings)
        bad(b'dave', range(10))
        bad(b'dave', map(str, lst))


class WriterNativeInterfaceDjbHashTestCase(WriterNativeInterfaceTestBase,
                                           unittest.TestCase):
    HASHFN = staticmethod(cdblib.djb_hash)


class Writer64NativeInterfaceDjbHashTestCase(WriterNativeInterfaceTestBase,
                                             unittest.TestCase):
    reader_cls = cdblib.Reader64
    writer_cls = cdblib.Writer64
    HASHFN = staticmethod(cdblib.djb_hash)


class WriterNativeInterfaceNativeHashTestCase(WriterNativeInterfaceTestBase,
                                              unittest.TestCase):
    HASHFN = staticmethod(hash)


class Writer64NativeInterfaceNativeHashTestCase(WriterNativeInterfaceTestBase,
                                                unittest.TestCase):
    reader_cls = cdblib.Reader64
    writer_cls = cdblib.Writer64
    HASHFN = staticmethod(hash)


class WriterNativeInterfaceNullHashTestCase(WriterNativeInterfaceTestBase,
                                            unittest.TestCase):
    HASHFN = staticmethod(lambda s: 1)


class WriterNativeInterfaceNullHashTestCase(WriterNativeInterfaceTestBase,
                                            unittest.TestCase):
    reader_cls = cdblib.Reader64
    writer_cls = cdblib.Writer64
    HASHFN = staticmethod(lambda s: 1)


class WriterKnownGoodTestBase(object):
    reader_cls = cdblib.Reader
    writer_cls = cdblib.Writer

    top250_path = 'testdata/top250pws.cdb'
    pwdump_path = 'testdata/pwdump.cdb'

    def setUp(self):
        self.sio = io.BytesIO()
        self.writer = self.writer_cls(self.sio, hashfn=self.HASHFN)

    def get_md5(self):
        self.writer.finalize()
        return hashlib.md5(self.sio.getvalue()).hexdigest()

    def test_empty(self):
        self.assertEqual(self.get_md5(), self.EMPTY_MD5)

    def test_single_rec(self):
        self.writer.put(b'dave', b'dave')
        self.assertEqual(self.get_md5(), self.SINGLE_REC_MD5)

    def test_dup_keys(self):
        self.writer.puts(b'dave', (b'dave', b'dave'))
        self.assertEqual(self.get_md5(), self.DUP_KEYS_MD5)

    def get_iteritems(self, filename):
        with io.open(filename, 'rb') as infile:
            data = infile.read()

        reader = self.reader_cls(data, hashfn=self.HASHFN)
        return reader.iteritems()

    def test_known_good_top250(self):
        for key, value in self.get_iteritems(self.top250_path):
            self.writer.put(key, value)
        self.assertEqual(self.get_md5(), self.TOP250PWS_MD5)

    def test_known_good_pwdump(self):
        for key, value in self.get_iteritems(self.pwdump_path):
            self.writer.put(key, value)
        self.assertEqual(self.get_md5(), self.PWDUMP_MD5)


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
    top250_path = 'testdata/top250pws.cdb64'
    pwdump_path = 'testdata/pwdump.cdb64'

    EMPTY_MD5 = 'c43c406a037989703e0d58ed9f17ba3c'
    SINGLE_REC_MD5 = '276ae8223f730b1e67007641db6b69ca'
    DUP_KEYS_MD5 = '1aae63d751ce5eea9e61916ae0aa00b3'
    TOP250PWS_MD5 = 'c6bdb3c7645c5d62747ac74895f9e90a'
    PWDUMP_MD5 = '3b1b4964294897c6ca119a6c6ae0094f'


@unittest.skipIf(six.PY3, 'Python 3.3+ use random hash seeds')
class WriterKnownGoodNativeHashTestCase(WriterKnownGoodTestBase,
                                        unittest.TestCase):
    HASHFN = staticmethod(hash)

    EMPTY_MD5 = 'a646d6b87720195feb973de130b10123'
    SINGLE_REC_MD5 = '9121969c106905e3fd72162c7bbb96a8'
    DUP_KEYS_MD5 = '331840e761aee9092af6f8b0370b7d9a'
    TOP250PWS_MD5 = 'e641b7b7d109b2daaa08335a1dc457c6'
    PWDUMP_MD5 = 'd5726fc195460c9eef3117111975532f'


@unittest.skipIf(six.PY3, 'Python 3.3+ use random hash seeds')
class Writer64KnownGoodNativeHashTestCase(WriterKnownGoodTestBase,
                                          unittest.TestCase):
    HASHFN = staticmethod(hash)
    reader_cls = cdblib.Reader64
    writer_cls = cdblib.Writer64
    top250_path = 'testdata/top250pws.cdb64'
    pwdump_path = 'testdata/pwdump.cdb64'

    EMPTY_MD5 = 'c43c406a037989703e0d58ed9f17ba3c'
    SINGLE_REC_MD5 = 'fdd4a8c055d2000cba9b712ceb8a1eba'
    DUP_KEYS_MD5 = '01e40b34cc51906f798233a2cd0fb09d'
    TOP250PWS_MD5 = '3cd101954030b153584b620db5255b45'
    PWDUMP_MD5 = 'a7275f527d54f51c10aebafaae1ab445'


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
    top250_path = 'testdata/top250pws.cdb64'
    pwdump_path = 'testdata/pwdump.cdb64'

    EMPTY_MD5 = 'c43c406a037989703e0d58ed9f17ba3c'
    SINGLE_REC_MD5 = '91f0614d6ec48e720138d6e962062166'
    DUP_KEYS_MD5 = 'e1fe0e8ae7bacd9dbe6a87cfccc627fa'
    TOP250PWS_MD5 = '25519af3e573e867f423956fc6e9b8e8'
    PWDUMP_MD5 = '5a8d1dd40d82af01cbb23ceab16c1588'


if __name__ == '__main__':
    unittest.main()

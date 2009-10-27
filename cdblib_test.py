#!/usr/bin/env python2.5

import hashlib
import unittest

from functools import partial

import cdblib

try:
    from cStringIO import StringIO
except ImportError:
    from StringIO import StringIO


class DjbHashTestCase(unittest.TestCase):
    def test_known_good(self):
        self.assertEqual(cdblib.djb_hash('dave'), 2087378131L)

    def test_correct_wrapping(self):
        h = cdblib.djb_hash('davedavedavedavedave')
        self.assertEqual(h, 3529598163L)


class ReaderKnownGoodTestCase(unittest.TestCase):
    def reader_to_cdbmake_md5(self, filename):
        md5 = hashlib.md5()
        for key, value in cdblib.Reader(fileobj=file(filename)).iteritems():
            md5.update('+%d,%d:%s->%s\n' % (len(key), len(value),
                                            key, value))
        md5.update('\n')

        return md5.hexdigest()

    def test_read_pwdump(self):
        # MD5s here are of the source .cdbmake file.
        self.assertEqual(self.reader_to_cdbmake_md5('testdata/pwdump.cdb'),
                         '84d38c5b6b5bb01bb374b2f7af0129b1')
        self.assertEqual(self.reader_to_cdbmake_md5('testdata/top250pws.cdb'),
                         '0564adfe4667506a326ba2f363415616')


class ReaderDictLikeTestCase(unittest.TestCase):
    def setUp(self):
        self.reader = cdblib.Reader(fileobj=file('testdata/top250pws.cdb'))

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
            self.assert_(type(self.reader[key]) is str)

    def test___iter__(self):
        for key in self.reader:
            self.assert_(type(self.reader[key]) is str)

    def test_values_itervalues(self):
        inverted = dict((v, k) for (k, v) in self.reader.iteritems())
        for value in self.reader.itervalues():
            self.assert_(value in inverted)
            self.assertEqual(self.reader[inverted[value]], value)

    def test_keys(self):
        self.assertEqual(self.reader.keys(), list(self.reader.iterkeys()))

    def test_values(self):
        self.assertEqual(self.reader.values(), list(self.reader.itervalues()))

    def test_has_key_contains(self):
        for key in self.reader:
            self.assert_(self.reader.has_key(key))
            self.assert_(key in self.reader)

        for key in ('zarg zarg warf!', 'doesnt exist really'):
            self.assertFalse(self.reader.has_key(key))
            self.assertFalse(key in self.reader)
            # there's no __notcontains__, right?
            self.assertTrue(key not in self.reader)

    def test_len(self):
        self.assertEqual(len(self.reader), 250)
        self.assertEqual(len(list(self.reader)), 250)

    def test_get_no_default(self):
        get = self.reader.get

        self.assertEqual(get('123456'), '1')
        self.assertEqual(get('love'), '12')
        self.assertRaises(KeyError, get, '!!KinDaCompleX')
        self.assertRaises(KeyError, get, '^^Hashes_Differently')

    def test_get_default(self):
        get = self.reader.get

        self.assertEqual(get('123456', 'default'), '1')
        self.assertEqual(get('love', 'default'), '12')
        self.assertEqual(get('!!KinDaCompleX', 'default'), 'default')
        self.assertEqual(get('^^Hashes_Differently', 'default'), 'default')


class ReaderNativeInterfaceTestBase:
    ARTS = (u'\N{SNOWMAN}', u'\N{CLOUD}', u'\N{UMBRELLA}')

    def setUp(self):
        self.sio = sio = StringIO()
        writer = cdblib.Writer(sio, hashfn=self.HASHFN)
        writer.puts('dave', (str(i) for i in xrange(10)))
        writer.put('dave_no_dups', '1')
        writer.put('dave_hex', '0x1a')
        writer.putstrings('art', self.ARTS)
        writer.finalize()

        sio.seek(0)
        self.reader = cdblib.Reader(fileobj=sio, hashfn=self.HASHFN)

    def test_constructor_file_like(self):
        pass # done in setUp

    def test_constructor_sequence(self):
        reader = cdblib.Reader(sequence=self.sio.getvalue())
        self.assertEqual(self.reader.items(), reader.items())

    def test_insertion_order(self):
        keys  = ['dave'] * 10
        keys.append('dave_no_dups')
        keys.append('dave_hex')
        keys.extend('art' for art in self.ARTS)
        self.assertEqual(self.reader.keys(), keys)

    def test_get(self):
        # First get on a key should return its first inserted value.
        self.assertEqual(self.reader.get('dave'), str(0))
        self.assertEqual(self.reader.get('dave_no_dups'), '1')

        # Default.
        self.assertEqual(self.reader.get('junk', 'wad'), 'wad')
        self.assertRaises(KeyError, self.reader.get, 'junk')

    def test_gets(self):
        self.assertEqual(list(self.reader.gets('dave')),
                         map(str, range(10)))
        self.assertEqual(list(self.reader.gets('dave_no_dups')),
                         ['1'])
        self.assertEqual(list(self.reader.gets('art')),
                         [ s.encode('utf-8') for s in self.ARTS ])
        self.assertEqual(list(self.reader.gets('junk')), [])

    def test_getint(self):
        self.assertEqual(self.reader.getint('dave'), 0)
        self.assertEqual(self.reader.getint('dave_no_dups'), 1)
        self.assertEqual(self.reader.getint('dave_hex', 16), 26)
        self.assertRaises(ValueError, self.reader.getint, 'art')

        self.assertEqual(self.reader.get('junk', 1), 1)
        self.assertRaises(KeyError, self.reader.getint, 'junk')

    def test_getints(self):
        self.assertEqual(list(self.reader.getints('dave')), range(10))
        self.assertRaises(ValueError, list, self.reader.getints('art'))

        self.assertEqual(list(self.reader.getints('junk')), [])

    def test_getstring(self):
        self.assertEqual(self.reader.getstring('art'), u'\N{SNOWMAN}')
        self.assertEqual(type(self.reader.getstring('art')), unicode)
        self.assertRaises(KeyError, self.reader.getstring, 'junk')

        self.assertEqual(self.reader.getstring('junk', u'\N{COMET}'),
                         u'\N{COMET}')

    def test_getstrings(self):
        self.assertEqual(tuple(self.reader.getstrings('art')), self.ARTS)
        self.assert_(all(type(s) is unicode
                     for s in self.reader.getstrings('art')))
        self.assertEqual(list(self.reader.getstrings('junk')), [])


class ReaderNativeInterfaceDjbHashTestCase(ReaderNativeInterfaceTestBase,
                                           unittest.TestCase):
    HASHFN = staticmethod(cdblib.djb_hash)


class ReaderNativeInterfaceNativeHashTestCase(ReaderNativeInterfaceTestBase,
                                              unittest.TestCase):
    HASHFN = staticmethod(hash)


class ReaderNativeInterfaceNullHashTestCase(ReaderNativeInterfaceTestBase,
                                            unittest.TestCase):
    # Ensure collisions don't result in the wrong keys being returned.
    HASHFN = staticmethod(lambda s: 1)


class WriterNativeInterfaceTestBase:
    def setUp(self):
        self.fp = StringIO()
        self.writer = cdblib.Writer(self.fp, hashfn=self.HASHFN)

    def get_reader(self):
        self.writer.finalize()
        self.fp.seek(0)
        return cdblib.Reader(fileobj=self.fp, hashfn=self.HASHFN)

    def make_bad(self, method):
        return partial(self.assertRaises, Exception, method)

    def test_put(self):
        self.writer.put('dave', 'dave')
        self.assertEqual(self.get_reader().get('dave'), 'dave')

        # Don't care about rich error, just as long as it crashes.
        bad = self.make_bad(self.writer.put)
        bad('dave', u'dave')
        bad(u'dave', 'dave')
        bad('dave', 123)
        bad(123, 'dave')

    def test_puts(self):
        lst = 'dave dave dave'.split()

        self.writer.puts('dave', lst)
        self.assertEqual(list(self.get_reader().gets('dave')), lst)

        bad = self.make_bad(self.writer.puts)
        bad('dave', map(unicode, lst))
        bad(u'dave', lst)
        bad('dave', (123,))
        bad(123, lst)

    def test_putkey(self):
        self.writer.putkey('dave')
        reader = self.get_reader()
        self.assert_('dave' in reader)
        self.assertEqual(reader['dave'], '')

        bad = self.make_bad(self.writer.putkey)
        bad(123)
        bad(u'dave')
        bad(True)

    def test_putint(self):
        self.writer.putint('dave', 26)
        self.writer.putint('dave2', 26<<32)
        self.assertEqual(self.get_reader().getint('dave'), 26)
        self.assertEqual(self.get_reader().getint('dave2'), 26<<32)

        bad = self.make_bad(self.writer.putint)
        bad(True)
        bad('dave')
        bad(None)

    def test_putints(self):
        self.writer.putints('dave', range(10))
        self.assertEqual(list(self.get_reader().getints('dave')), range(10))

        bad = self.make_bad(self.writer.putints)
        bad((True, False))
        bad('dave')
        bad(u'dave')

    def test_putstring(self):
        self.writer.putstring('dave', u'dave')
        self.assertEqual(self.get_reader().getstring('dave'), u'dave')

        bad = self.make_bad(self.writer.putstring)
        bad('dave')
        bad(123)
        bad(None)

    def test_putstrings(self):
        lst = [u'zark', u'quark']
        self.writer.putstrings('dave', lst)
        self.assertEqual(list(self.get_reader().getstrings('dave')), lst)

        bad = self.make_bad(self.writer.putstrings)
        bad('dave', range(10))
        bad('dave', map(str, lst))


class WriterNativeInterfaceDjbHashTestCase(WriterNativeInterfaceTestBase,
                                           unittest.TestCase):
    HASHFN = staticmethod(cdblib.djb_hash)


class WriterNativeInterfaceNativeHashTestCase(WriterNativeInterfaceTestBase,
                                              unittest.TestCase):
    HASHFN = staticmethod(hash)


class WriterNativeInterfaceNullHashTestCase(WriterNativeInterfaceTestBase,
                                            unittest.TestCase):
    HASHFN = staticmethod(lambda s: 1)


class WriterKnownGoodTestBase:
    def setUp(self):
        self.fp = StringIO()
        self.writer = cdblib.Writer(self.fp, hashfn=self.HASHFN)

    def get_md5(self):
        self.writer.finalize()
        return hashlib.md5(self.fp.getvalue()).hexdigest()

    def test_empty(self):
        self.assertEqual(self.get_md5(), self.EMPTY_MD5)

    def test_single_rec(self):
        self.writer.put('dave', 'dave')
        self.assertEqual(self.get_md5(), self.SINGLE_REC_MD5)

    def test_dup_keys(self):
        self.writer.puts('dave', ('dave', 'dave'))
        self.assertEqual(self.get_md5(), self.DUP_KEYS_MD5)

    def get_iteritems(self, filename):
        reader = cdblib.Reader(fileobj=file(filename), hashfn=self.HASHFN)
        return reader.iteritems()

    def test_known_good_top250(self):
        for key, value in self.get_iteritems('testdata/top250pws.cdb'):
            self.writer.put(key, value)
        self.assertEqual(self.get_md5(), self.TOP250PWS_MD5)

    def test_known_good_pwdump(self):
        for key, value in self.get_iteritems('testdata/pwdump.cdb'):
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


class WriterKnownGoodNativeHashTestCase(WriterKnownGoodTestBase,
                                        unittest.TestCase):
    HASHFN = staticmethod(hash)

    EMPTY_MD5 = 'a646d6b87720195feb973de130b10123'
    SINGLE_REC_MD5 = '9121969c106905e3fd72162c7bbb96a8'
    DUP_KEYS_MD5 = '331840e761aee9092af6f8b0370b7d9a'
    TOP250PWS_MD5 = 'e641b7b7d109b2daaa08335a1dc457c6'
    PWDUMP_MD5 = 'd5726fc195460c9eef3117111975532f'


class WriterKnownGoodNullHashTestCase(WriterKnownGoodTestBase,
                                      unittest.TestCase):
    HASHFN = staticmethod(lambda s: 1)

    EMPTY_MD5 = 'a646d6b87720195feb973de130b10123'
    SINGLE_REC_MD5 = 'f8cc0cdd90fe45193f7d53980c354d5f'
    DUP_KEYS_MD5 = '3d5ad135593c942cf9621d3d4a1f6637'
    TOP250PWS_MD5 = '0a5fff8836a175460ead340afff2d301'
    PWDUMP_MD5 = 'eac33af35208c7daba0487d0d411b8d5'


if __name__ == '__main__':
    unittest.main()

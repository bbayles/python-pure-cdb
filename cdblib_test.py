#!/usr/bin/env python2.5

import hashlib
import unittest

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


class MightMaskTestCase(unittest.TestCase):
    def test_no_wrap(self):
        self.assert_(cdblib.might_mask(hash, hash('dave')) is hash)

    def test_wrap(self):
        h = hash('dave') | (1<<32)
        self.assert_(cdblib.might_mask(hash, h)('dave') == 841352530)


class ReaderKnownGoodTestCase(unittest.TestCase):
    def reader_to_cdbmake_md5(self, filename):
        md5 = hashlib.md5()
        for key, value in cdblib.Reader(file(filename)).iteritems():
            md5.update('+%d,%d:%s->%s\n' % (len(key), len(value),
                                            key, value))
        md5.update('\n')

        return md5.hexdigest()

    def test_read_pwdump(self):
        # MD5s here are of the source .cdbmake file.
        self.assertEqual(self.reader_to_cdbmake_md5('testdata/pwdump.cdb'),
                         'e4ba0fa6c6283875b757d36db36f3f5c')
        self.assertEqual(self.reader_to_cdbmake_md5('testdata/top250pws.cdb'),
                         '0564adfe4667506a326ba2f363415616')


class ReaderDictLikeTestCase(unittest.TestCase):
    def setUp(self):
        self.reader = cdblib.Reader(file('testdata/top250pws.cdb'))

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

    def test_keys_iterkeys(self):
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
        fp = StringIO()
        writer = cdblib.Writer(fp, hash=self.HASH_FUNCTION)
        writer.puts('dave', (str(i) for i in xrange(10)))
        writer.put('dave_no_dups', '1')
        writer.putstrings('art', self.ARTS)
        writer.finalize()

        fp.seek(0)
        self.reader = cdblib.Reader(fp, hash=self.HASH_FUNCTION)

    def test_insertion_order(self):
        keys  = ['dave'] * 10
        keys.append('dave_no_dups')
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
        self.assertRaises(ValueError, self.reader.getstring, 'junk')

        self.assertEqual(self.reader.getstring('junk', u'\N{COMET}'),
                         u'\N{COMET}')

    def test_getstrings(self):
        self.assertEqual(tuple(self.reader.getstrings('art')), self.ARTS)
        self.assert_(all(type(s) is unicode
                     for s in self.reader.getstrings('art')))
        self.assertEqual(list(self.reader.getstrings('junk')), [])


class ReaderNativeInterfaceDjbHashTestCase(ReaderNativeInterfaceTestBase,
                                           unittest.TestCase):
    HASH_FUNCTION = staticmethod(cdblib.djb_hash)


class ReaderNativeInterfaceNativeHashTestCase(ReaderNativeInterfaceTestBase,
                                              unittest.TestCase):
    HASH_FUNCTION = staticmethod(hash)


class ReaderNativeInterfaceNullHashTestCase(ReaderNativeInterfaceTestBase,
                                            unittest.TestCase):
    # Ensure collisions don't result in the wrong keys being returned.
    @staticmethod
    def HASH_FUNCTION(s):
        return 1


class WriterTestBase:
    def setUp(self):
        self.fp = StringIO()
        self.writer = cdblib.Writer(self.fp, hash=self.HASH_FUNCTION)

    def get_md5(self):
        self.writer.finalize()
        return hashlib.md5(self.fp.getvalue()).hexdigest()

    def test_known_good(self):
        self.writer.put('dave', 'dave')
        self.assertEqual(self.get_md5(), self.DAVE_DAVE_MD5)

    def test_known_good_multikey(self):
        self.writer.puts('dave', ('dave', 'dave'))
        self.assertEqual(self.get_md5(), self.DAVE_DAVE_DAVE_MD5)


class WriterDjbHashTestCase(WriterTestBase, unittest.TestCase):
    HASH_FUNCTION = staticmethod(cdblib.djb_hash)
    DAVE_DAVE_MD5 = 'd94cdc896807d5b7ab5be0078d1469dc'
    DAVE_DAVE_DAVE_MD5 = 'cb67e9e167cefcaddf62f03baa7f6c72'

class WriterNativeHashTestCase(WriterTestBase, unittest.TestCase):
    HASH_FUNCTION = staticmethod(hash)
    DAVE_DAVE_MD5 = ''
    DAVE_DAVE_DAVE_MD5 = ''

class WriterNullHashTestCase(WriterTestBase, unittest.TestCase):
    @staticmethod
    def HASH_FUNCTION(s):
        return 1

    DAVE_DAVE_MD5 = 'f8cc0cdd90fe45193f7d53980c354d5f'
    DAVE_DAVE_DAVE_MD5 = 'd0b29c95509ce78594f9a69ff0818073'


class WriterKnownGoodTestCase(unittest.TestCase):
    pass


if __name__ == '__main__':
    unittest.main()

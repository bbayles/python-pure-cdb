#!/usr/bin/env python2.5

import hashlib
import unittest

import cdblib


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
        all = dict(self.reader.iteritems())
        inverted = dict((v, k) for (k, v) in all.iteritems())

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


class ReaderNativeInterfaceTestCase(unittest.TestCase):
    pass


if __name__ == '__main__':
    unittest.main()

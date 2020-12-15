#!/usr/bin/env python
from __future__ import division, print_function, unicode_literals
import unittest

from os.path import exists, join
from shutil import rmtree
from tempfile import mkdtemp

try:
    import cdb
    test_cdb = True
except ImportError:
    import cdblib.compat as cdb
    test_cdb = False

from tests.test_cdblib import testdata_path


class CompatTests(object):
    def setUp(self):
        self.temp_dir = mkdtemp()
        self.cdb_path = join(self.temp_dir, 'database.cdb')
        self.tmp_path = join(self.temp_dir, 'database.tmp')

        self.db = cdb.cdbmake(
            self.cdb_path.encode('utf-8'), self.tmp_path.encode('utf-8')
        )
        self.db.add('a', '1')
        self.db.add('a', '2')
        self.db.addmany([('b', '1'), ('c', '1')])
        self.db.add('a', b'\x80')

    def tearDown(self):
        rmtree(self.temp_dir, ignore_errors=False)

    def _get_reader(self, **kwargs):
        self.db.finish()
        return cdb.init(self.cdb_path.encode('utf-8'), **kwargs)

    def test_add(self):
        self.db.add('a', '4')
        self.assertEqual(self.db.numentries, 6)
        self.db.add('a', '4')
        self.assertEqual(self.db.numentries, 7)

        with self.assertRaises(TypeError):
            self.db.add(1, '1')

    def test_numentries(self):
        self.assertEqual(self.db.numentries, 5)
        self.db.finish()
        self.assertEqual(self.db.numentries, 5)

    def test_cdbmake_fd(self):
        self.assertTrue(isinstance(self.db.fd, int))

    def test_finish(self):
        self.db.finish()
        self.assertFalse(exists(self.tmp_path))

    def test_get(self):
        reader = self._get_reader()
        self.assertEqual(reader.get('a'), '1')
        self.assertEqual(reader.get('a', 1), '2')
        self.assertEqual(reader.get('a', 2), b'\x80')
        self.assertEqual(reader.get('a', 3), None)

    def test_getitem(self):
        reader = self._get_reader()
        self.assertEqual(reader['a'], '1')
        self.assertEqual(reader['b'], '1')
        self.assertEqual(reader['c'], '1')

        with self.assertRaises(KeyError):
            reader['d']

    def test_getall(self):
        reader = self._get_reader()
        self.assertEqual(reader.getall('a'), ['1', '2', b'\x80'])
        self.assertEqual(reader.getall('b'), ['1'])
        self.assertEqual(reader.getall('c'), ['1'])
        self.assertEqual(reader.getall('d'), [])

    def test_each(self):
        reader = self._get_reader()
        self.assertEqual(reader.each(), ('a', '1'))
        self.assertEqual(reader.each(), ('a', '2'))
        self.assertEqual(reader.each(), ('b', '1'))
        self.assertEqual(reader.each(), ('c', '1'))
        self.assertEqual(reader.each(), ('a', b'\x80'))
        self.assertIsNone(reader.each())
        self.assertEqual(reader.each(), ('a', '1'))

    def test_firstkey(self):
        reader = self._get_reader()
        self.assertEqual(reader.firstkey(), 'a')
        self.assertEqual(reader.nextkey(), 'b')
        self.assertEqual(reader.firstkey(), 'a')
        self.assertEqual(reader.nextkey(), 'b')

    def test_nextkey(self):
        reader = self._get_reader()
        self.assertEqual(reader.nextkey(), 'a')
        self.assertEqual(reader.nextkey(), 'b')
        self.assertEqual(reader.nextkey(), 'c')
        self.assertIsNone(reader.nextkey())
        self.assertIsNone(reader.nextkey())

    def test_keys(self):
        reader = self._get_reader()
        self.assertEqual(reader.keys(), ['a', 'b', 'c'])

    def test_name_size_fd(self):
        reader = self._get_reader()
        self.assertEqual(reader.name.decode('utf-8'), self.cdb_path)
        self.assertEqual(reader.size, 2178)
        self.assertTrue(isinstance(reader.fd, int))


@unittest.skipIf(not test_cdb, 'Tests for Python 2 module')
class PythonCDBTests(CompatTests, unittest.TestCase):
    pass


@unittest.skipIf(test_cdb, 'Tests for Python 3 module')
class PythonPureCDBTests(CompatTests, unittest.TestCase):
    def test_cdbmake_cleanup(self):
        # Cleanup after close - no exception
        self.db.finish()
        self.db.finish()
        self.db._cleanup()

        # Exception during cleanup - we soldier on
        self.db._temp_obj = None
        self.db._cleanup()

    def test_add_after_finish(self):
        self.db.finish()
        with self.assertRaises(cdb.error):
            self.db.add('d', '1')

    def test_cdb_cleanup(self):
        # Cleanup after close - no exception
        reader = self._get_reader()
        reader._mmap_obj.close()
        reader._file_obj.close()
        reader._cleanup()

        reader._mmap_obj = None
        reader._file_obj = None

        # Exception during cleanup - we soldier on
        reader._cleanup()

    def test_no_encoding(self):
        reader = self._get_reader(encoding=None)
        self.assertEqual(reader.get(b'a'), b'1')
        self.assertEqual(reader.getall(b'a'), [b'1', b'2', b'\x80'])
        self.assertEqual(reader.keys(), [b'a', b'b', b'c'])


if __name__ == '__main__':
    unittest.main()

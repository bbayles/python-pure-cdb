#!/usr/bin/env python
from __future__ import division, print_function, unicode_literals
import unittest

from os.path import exists, join
from shutil import rmtree
from tempfile import mkdtemp

try:
    import cdb
except ImportError:
    import cdblib.compat as cdb

from tests.cdblib_test import testdata_path


class CompatTests(unittest.TestCase):
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

    def _get_reader(self):
        self.db.finish()
        return cdb.init(self.cdb_path.encode('utf-8'))

    def test_add(self):
        self.db.add('a', '4')
        self.db.add('a', '4')

    def test_numentries(self):
        self.assertEqual(self.db.numentries, 5)
        self.db.finish()
        self.assertEqual(self.db.numentries, 5)

    def test_finish(self):
        self.db.finish()
        self.assertFalse(exists(self.tmp_path))

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

    def test_size(self):
        reader = self._get_reader()
        self.assertEqual(reader.size, 2178)


if __name__ == '__main__':
    unittest.main()

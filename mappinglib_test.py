#!/usr/bin/env python2.5

import sys
import unittest

from mappinglib import *


def lst_dump(lst, fp=sys.stdout):
    its = [(' FORWARD ', lst_iter(lst_head(lst))),
           (' REVERSE ', lst_iter(lst_tail(lst), reverse=True))]
    high = idx = 0
    for title, it in its:
        print >>fp, title.center(70, '-')
        for idx, node in enumerate(it):
            print >>fp, ' %-5d I=%-8x P=%-8x N=%-8x %.20r' %\
                (abs(high-idx),
                 id(node) if node else 0,
                 id(node[0]) if node[0] else 0,
                 id(node[2]) if node[2] else 0,
                 node[1])
        print >>fp, '-' * 70
        print >>fp
        high = max(high, idx)


def lst_check(lst):
    fwd_len = len(list(lst_iter(lst_head(lst))))
    rev_len = len(list(lst_iter(lst_tail(lst), reverse=True)))

    assert fwd_len == rev_len, \
           'Forward iter yields %d items, reverse yields %d'\
           % (fwd_len, rev_len)

    if fwd_len in (0, 1):
        assert lst[0] == lst[1], \
               '%d-sized list yet head != tail' % (fwd_len,)
    else:
        assert lst[0] != lst[1], \
               '%d-sized list yet head == head' % (fwd_len,)

    fwd_nodes = list(lst_iter(lst_head(lst)))
    rev_nodes = list(lst_iter(lst_tail(lst), reverse=True))

    fwd_vals = [n[1] for n in fwd_nodes]
    rev_vals = [n[1] for n in reversed(rev_nodes)]

    assert all(x is y
               for (x, y) in zip(fwd_nodes, reversed(rev_nodes))),\
           'Forward and reverse walk do not match'


class ListTestCase(unittest.TestCase):
    def setUp(self):
        self.lst = lst_new()

    def test_append_one(self):
        node = lst_append(self.lst, 'value')
        self.assert_(lst_head(self.lst) is node)
        self.assert_(lst_tail(self.lst) is node)
        self.assert_(lst_value(lst_head(self.lst)) == 'value')
        self.assert_(lst_value(lst_tail(self.lst)) == 'value')
        lst_check(self.lst)

        lst_unlink(self.lst, node)
        self.assert_(lst_head(self.lst) is None)
        self.assert_(lst_tail(self.lst) is None)
        lst_check(self.lst)

    def test_append_two(self):
        node1 = lst_append(self.lst, 'value1')
        node2 = lst_append(self.lst, 'value2')
        lst_check(self.lst)

        self.assert_(lst_head(self.lst) is node1)
        self.assert_(lst_next(lst_head(self.lst)) is node2)
        self.assert_(lst_next(lst_next(lst_head(self.lst))) is None)

        self.assert_(lst_tail(self.lst) is node2)
        self.assert_(lst_prev(self.lst) is node1)
        self.assert_(lst_prev(lst_prev(self.lst)) is None)

        self.assert_(lst_value(lst_head(self.lst)) == 'value1')
        self.assert_(lst_value(lst_next(lst_head(self.lst))) == 'value2')
        self.assert_(lst_value(lst_next(lst_next(lst_head(self.lst)))) is None)

    def test_empty(self):
        self.assert_(lst_head(self.lst) is None)
        self.assert_(lst_tail(self.lst) is None)
        self.assert_(lst_value(lst_head(self.lst)) is None)
        self.assert_(lst_value(lst_tail(self.lst)) is None)

    def test_prepend_one(self):
        node = lst_prepend(self.lst, 'value')
        self.assert_(lst_head(self.lst) is node)
        self.assert_(lst_tail(self.lst) is node)
        self.assert_(lst_value(lst_head(self.lst)) == 'value')
        self.assert_(lst_value(lst_tail(self.lst)) == 'value')
        lst_check(self.lst)

    def test_prepend_two(self):
        node2 = lst_prepend(self.lst, 'value2')
        node1 = lst_prepend(self.lst, 'value1')
        lst_check(self.lst)

        self.assert_(lst_head(self.lst) is node1)
        self.assert_(lst_next(lst_head(self.lst)) is node2)
        self.assert_(lst_next(lst_next(lst_head(self.lst))) is None)

        self.assert_(lst_tail(self.lst) is node2)
        self.assert_(lst_prev(lst_tail(self.lst)) is node1)
        self.assert_(lst_prev(lst_prev(lst_tail(self.lst))) is None)

        self.assert_(lst_value(lst_head(self.lst)) == 'value1')
        self.assert_(lst_value(lst_next(lst_head(self.lst))) == 'value2')
        self.assert_(lst_value(lst_next(lst_next(lst_head(self.lst)))) is None)

    def test_prepend_append(self):
        node1 = lst_prepend(self.lst, 'value1')
        node2 = lst_append(self.lst, 'value2')

        self.assert_(lst_head(self.lst) is node1)
        self.assert_(lst_next(lst_head(self.lst)) is node2)

        self.assert_(lst_tail(self.lst) is node2)
        self.assert_(lst_prev(lst_tail(self.lst)) is node1)

    def test_unlink_one(self):
        node = lst_prepend(self.lst, 'value')
        lst_unlink(self.lst, node)

        self.assert_(lst_head(self.lst) is None)
        self.assert_(lst_tail(self.lst) is None)

    def test_unlink_two(self):
        node1 = lst_append(self.lst, 'value1')
        node2 = lst_append(self.lst, 'value2')
        lst_check(self.lst)

        lst_unlink(self.lst, node2)
        self.assert_(lst_tail(self.lst) is node1)
        self.assert_(lst_head(self.lst) is node1)
        lst_check(self.lst)

        lst_unlink(self.lst, node1)
        self.assert_(lst_tail(self.lst) is None)
        self.assert_(lst_head(self.lst) is None)
        lst_check(self.lst)

    def test_unlink_three(self):
        lst_append(self.lst, 'value1')
        lst_check(self.lst)
        lst_append(self.lst, 'value2')
        lst_check(self.lst)
        lst_append(self.lst, 'value3')
        lst_check(self.lst)
        lst_unlink(self.lst, lst_tail(self.lst))
        lst_check(self.lst)


class LruCacheTestCase(unittest.TestCase):
    def test_one(self):
        cache = LruCache(1)

        self.assert_(cache.get('key1') is None)
        cache.put('key1', 'value1')
        self.assert_(cache.get('key1') == 'value1')

        cache.put('key2', 'value2')
        self.assert_(cache.get('key1') is None)
        self.assert_(cache.get('key2') == 'value2')

    def test_lru(self):
        cache = LruCache(3)

        cache.put('key1', 'value1')
        cache.put('key2', 'value2')
        cache.put('key3', 'value3')

        cache.put('key4', 'value4')
        self.assert_(cache.get('key1') is None)
        self.assert_(cache.get('key2') == 'value2')
        self.assert_(cache.get('key3') == 'value3')
        self.assert_(cache.get('key4') == 'value4')

        # This time, change the order we check in.
        cache.put('key5', 'value5')
        self.assert_(cache.get('key5') == 'value5')
        self.assert_(cache.get('key4') == 'value4')
        self.assert_(cache.get('key3') == 'value3')
        self.assert_(cache.get('key2') is None)
        self.assert_(cache.get('key1') is None)

        # key5 is the LRU after previous gets.
        cache.put('key6', 'value6')
        self.assert_(cache.get('key6') == 'value6')
        self.assert_(cache.get('key5') is None)
        self.assert_(cache.get('key4') == 'value4')
        self.assert_(cache.get('key3') == 'value3')
        self.assert_(cache.get('key2') is None)
        self.assert_(cache.get('key1') is None)


if __name__ == '__main__':
    unittest.main()

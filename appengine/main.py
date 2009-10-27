#!/usr/bin/env python

import wsgiref.handlers

import logging
import random

from cStringIO import StringIO
from time import time

from google.appengine.ext import webapp

import cdblib


def stopwatch(fn, cleanup=lambda: None, repeat=1000):
    all = 0

    for i in xrange(repeat):
        logging.info('-- run %d', i)
        cleanup()
        t1 = time()
        fn()
        t2 = time()
        all += int((t2 * 10000) - (t1 * 1000000))

    return all / repeat


class PerfHandler(webapp.RequestHandler):
    def test_put1(self):
        key, value = self.reader.iteritems().next()
        def put1():
            self.writer.put(key, key)
        return stopwatch(put1)

    def test_put100(self):
        items = self.reader.items()[:100]
        def put100():
            for item in items:
                self.writer.put(*item)
        return stopwatch(put100, cleanup=self.new_writer)

    def test_putfull(self):
        items = self.reader.items()
        def putfull():
            for item in items:
                self.writer.put(*item)
        return stopwatch(putfull, cleanup=self.new_writer)

    def trunc(self):
        self.sio.seek(0)
        self.sio.truncate(0)

    def test_final1(self):
        self.writer.put(*random.choice(self.reader.items()))
        def final1():
            self.writer.put(key, value)
            self.writer.finalize()
        return stopwatch(final1, cleanup=self.trunc)

    def test_final100(self):
        items = self.reader.items()[:100]
        self.new_writer()
        for item in items:
            self.writer.put(*item)
        return stopwatch(self.writer.finalize, cleanup=self.trunc)

    def test_open1(self):
        self.writer.write('12312312', '32131312')
        self.writer.finalize()
        def open1():
            self.sio.seek(0)
            cdblib.Reader(self.sio, self.hashfn)
        return stopwatch(open1)

    def test_open100(self):
        for key, value in self.reader.items()[:100]:
           self.writer.write(key, value)
        self.writer.finalize()
        def open100():
            self.sio.seek(0)
            cdblib.Reader(self.sio, self.hashfn)
        return stopwatch(open100)

    def test_openfull(self):
        def openfull():
            self.cdb_fp.seek(0)
            cdblib.Reader(self.cdb_fp)
        return stopwatch(openfull)

    def copy(self):
        writer = cdblib.Writer(StringIO(), self.hashfn)
        for key, value in self.reader.iteritems():
            writer.put(key, value)
        writer.finalize()
        return cdblib.Reader(writer.fp, self.hashfn)

    def test_randget1(self):
        keys = self.reader.keys()
        reader2 = self.copy()
        def randget1():
            reader2[random.choice(keys)]
        return stopwatch(randget1)

    def test_repeatget1(self):
        key = random.choice(self.reader.keys())
        reader2 = self.copy()
        def repeatget1():
            reader2[key]
        return stopwatch(repeatget1)

    def test_repeatget100(self):
        reader2 = self.copy()

        keys = self.reader.keys()
        random.shuffle(keys)
        keys = keys[:100]
        def repeatget100():
            for key in keys:
                reader2[key]
        return stopwatch(repeatget100)

    def test_iteritems(self):
        return stopwatch(self.copy().items)

    def new_writer(self):
        self.sio = StringIO()
        self.writer = cdblib.Writer(self.sio, self.hashfn)

    def get(self):
        test = self.request.get('test')
        data = self.request.get('db')
        hashfn = self.request.get('hashfn')

        if self.request.get('hashfn') == 'djb':
            self.hashfn = cdblib.djb_hash
        else:
            self.hashfn = hash

        self.cdb_fp = file('testdata/%s.cdb' % data)
        self.reader = cdblib.Reader(self.cdb_fp)
        self.new_writer()

        per_run_us = getattr(self, 'test_' + test)()
        self.response.out.write(str(per_run_us))


def main():
    app = webapp.WSGIApplication([('/perf', PerfHandler)], debug=True)
    wsgiref.handlers.CGIHandler().run(app)


if __name__ == '__main__':
    main()

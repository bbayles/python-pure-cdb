#!/usr/bin/env python
'''Python version of DJB's cdbmake, optionally supporting Python's hash().

Usage:
    cdbmake.py [-p] <output> <tmp>

Where:
    -p      Use Python hash() instead of standard DJB hash function.
    -8      Use cdblib.Writer64 rather than cdblib.Writer.
    output  Eventual destination path, must reside on same filesystem as tmp.
    tmp     Temporary file to use during write. Atomically replaces output at
            end.
'''
from __future__ import print_function

import getopt
import io
import os
import sys

from functools import partial

import cdblib


class CdbMake(object):
    def __init__(self, stdin, stdout, stderr):
        self.stdin = stdin
        self.stdout = stdout
        self.stderr = stderr
        self.python_hash = False
        self.writer_cls = cdblib.Writer
        self.encoding = sys.getdefaultencoding()

    def parse_args(self, args):
        try:
            opts, args = getopt.gnu_getopt(args, 'p8')
        except getopt.error as e:
            self.usage(str(e))

        for opt, arg in opts:
            if opt == '-p':
                self.python_hash = True
            elif opt == '-8':
                self.writer_cls = cdblib.Writer64

        if len(args) != 2:
            self.usage('Not enough or too many filenames.')

        self.filename = args[0]
        self.tmp_filename = args[1]

    def begin(self):
        hash_func = hash if self.python_hash else cdblib.djb_hash
        self.fp = io.open(self.tmp_filename, 'wb')
        self.writer = self.writer_cls(self.fp, hash_func)

    def parse_input(self):
        read = self.stdin.read
        rec_nr = 0

        while True:
            rec_nr += 1
            plus = read(1)
            if plus == '\n':
                return
            elif plus != '+':
                self.die('bad or missing plus, line/record #%d', rec_nr)

            try:
                klen = int(''.join(iter(partial(read, 1), ',')), 10)
                dlen = int(''.join(iter(partial(read, 1), ':')), 10)
            except ValueError:
                self.die('bad or missing length, line/record #%d', rec_nr)

            key = read(klen)
            if read(2) != '->':
                self.die('bad or missing separator, line/record #%d', rec_nr)

            data = read(dlen)
            if (len(key) + len(data)) != (klen + dlen):
                self.die('short key or data, line/record #%d', rec_nr)

            if read(1) != '\n':
                self.die('bad line ending, line/record #%d', rec_nr)

            self.writer.put(
                key.encode(self.encoding), data.encode(self.encoding)
            )

    def end(self):
        self.writer.finalize()
        os.fsync(self.fp.fileno())
        self.fp.close()
        os.rename(self.tmp_filename, self.filename)

    def die(self, fmt, *args):
        if args:
            fmt %= args
        self.stderr.write('Error: %s\n' % (fmt,))
        raise SystemExit(1)

    def usage(self, fmt, *args):
        print(__doc__)
        if fmt:
            self.die(fmt, *args)
        raise SystemExit(0)


def main(args=None, stdin=sys.stdin, stdout=sys.stdout, stderr=sys.stderr):
    args = sys.argv[1:] if (args is None) else args
    self = CdbMake(stdin, stdout, stderr)
    self.parse_args(args)
    self.begin()
    self.parse_input()
    self.end()


if __name__ == '__main__':
    main(sys.argv[1:])

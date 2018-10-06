from __future__ import print_function, unicode_literals

import argparse
import io
import os
import sys

import six

import cdblib


class CDBMaker(object):
    def __init__(self, parsed_args, **kwargs):
        # Read binary data from stdin and write errors to stderr (by default)
        self.stdin = kwargs.get('stdin')
        if self.stdin is None:
            self.stdin = sys.stdin if six.PY2 else sys.stdin.buffer

        self.stderr = kwargs.get('stderr', sys.stderr)

        # First we'll write to the cdb.tmp file, then replace it with the
        # cdb file
        self.cdb_temp_path = parsed_args['cdb.tmp']
        self.cdb_path = parsed_args['cdb']

        # Select writer class
        self.writer_cls = (
            cdblib.Writer64 if parsed_args['64'] else cdblib.Writer
        )

    def read_len(self, separator):
        # Read characters out of stdin up until separator, and then return
        # them interpreted as a base 10 integer.
        # If there's an error, return None.
        chars = []
        for c in iter(lambda: self.stdin.read(1), separator):
            if not c:
                return None
            chars.append(c)

        try:
            return int(b''.join(chars), 10)
        except ValueError:
            return None

    def fail(self, msg, record_number):
        print(
            'Error while parsing record {}: {}'.format(record_number, msg),
            file=self.stderr
        )
        sys.exit(1)

    def get_items(self):
        # Yield (key, data) pairs from the input
        record_number = 0
        while True:
            # Record starter: + character
            record_number += 1
            plus = self.stdin.read(1)
            if plus == b'\n':
                break
            elif plus != b'+':
                self.fail('Invalid start', record_number)

            # Key length - must be an integer ending with ,
            klen = self.read_len(b',')
            if klen is None:
                self.fail('Invalid klen', record_number)

            # Data length - must be an integer ending with :
            dlen = self.read_len(b':')
            if dlen is None:
                self.fail('Invalid dlen', record_number)

            # key->data\n
            key = self.stdin.read(klen)
            arrow = self.stdin.read(2)
            data = self.stdin.read(dlen)
            newline = self.stdin.read(1)

            if arrow != b'->':
                self.fail('Invalid separator', record_number)

            if len(key) + len(data) < klen + dlen:
                self.fail(
                    'Key or data did not match given length', record_number
                )

            if newline != b'\n':
                self.fail('Invalid character after record', record_number)

            yield key, data

    def run(self):
        with io.open(self.cdb_temp_path, 'wb') as tmpfile:
            with self.writer_cls(tmpfile) as writer:
                for key, data in self.get_items():
                    writer.put(key, data)

        os.rename(self.cdb_temp_path, self.cdb_path)


def main(args=None, **kwargs):
    args = sys.argv[1:] if (args is None) else args
    parser = argparse.ArgumentParser(
        description=(
            "Python version of djb's cdbmake. "
            "Supports standard 32-bit cdb files as well as 64-bit variants."
        )
    )
    parser.add_argument(
        '-64', action='store_true', help='Use non-standard 64-bit file offsets'
    )
    parser.add_argument(
        'cdb',
        help=(
            'Ultimate destination path for the constant database. '
            'This path is not overwritten to until all input has been '
            'validated and the cdb.tmp file is finalized.'
        ),
    )
    parser.add_argument(
        'cdb.tmp',
        help=(
            'Temporary path to use for the creating cdb file. '
            'This file will moved to the cdb path after it is finalized. '
            'It must be on the same filesystem as the cdb file.'
        )
    )

    parsed_args = vars(parser.parse_args(args))
    CDBMaker(parsed_args, **kwargs).run()


if __name__ == '__main__':
    main()

from __future__ import print_function

import argparse
import sys

import six

import cdblib


def cdbdump(parsed_args, **kwargs):
    # Read binary data from stdin by default
    stdin = kwargs.get('stdin')
    if stdin is None:
        stdin = sys.stdin if six.PY2 else sys.stdin.buffer

    # Print text data to stdout by default
    stdout = kwargs.get('stdout')
    if stdout is None:
        stdout = sys.stdout if six.PY2 else sys.stdout.buffer

    # Consume stdin and parse the cdb file
    reader_cls = cdblib.Reader64 if parsed_args['64'] else cdblib.Reader
    data = stdin.read()
    reader = reader_cls(data)

    # Dump the file's contents to the ouput stream
    for key, value in reader.iteritems():
        item = (
            b'+',
            str(len(key)).encode('ascii'),
            b',',
            str(len(value)).encode('ascii'),
            b':',
            key,
            b'->',
            value,
            b'\n',
        )
        stdout.write(b''.join(item))

    # Print final newline
    stdout.write(b'\n')


def main(args=None, **kwargs):
    args = sys.argv[1:] if (args is None) else args
    parser = argparse.ArgumentParser(
        description=(
            "Python version of djb's cdbdump. "
            "Supports standard 32-bit cdb files as well as 64-bit variants."
        )
    )
    parser.add_argument(
        '-64', action='store_true', help='Use non-standard 64-bit file offsets'
    )

    parsed_args = vars(parser.parse_args(args))
    cdbdump(parsed_args, **kwargs)


if __name__ == '__main__':
    main()

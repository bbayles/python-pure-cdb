from __future__ import unicode_literals

import six

# The cdb hash function is defined at: http://cr.yp.to/cdb/cdb.txt
# We use separate implementations for Python 2 and 3, since they treat
# iterating over byte strings differently.
if six.PY2:
    def djb_hash(s):
        '''Return the value of DJB's hash function for byte string *s*'''
        h = 5381
        for c in s:
            h = (((h << 5) + h) ^ ord(c)) & 0xffffffff
        return h
else:
    def djb_hash(s):  # noqa
        '''Return the value of DJB's hash function for byte string *s*'''
        h = 5381
        for c in s:
            h = (((h << 5) + h) ^ c) & 0xffffffff
        return h

# If the C Extensions is available (Python 2 only), use it
try:
    from ._djb_hash import djb_hash  # noqa
except ImportError:
    pass

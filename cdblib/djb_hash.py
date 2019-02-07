# The cdb hash function is defined at: http://cr.yp.to/cdb/cdb.txt
def djb_hash(s):  # noqa
    '''Return the value of DJB's hash function for byte string *s*'''
    h = 5381
    for c in s:
        h = (((h << 5) + h) ^ c) & 0xffffffff
    return h


# If the C Extension is available, use it
try:
    from ._djb_hash import djb_hash  # noqa
except ImportError:
    pass

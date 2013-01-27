#!/usr/bin/env python2.5

# Create a new lst.
lst_new = lambda: [None, None]

# Return the node at the head of lst, or None.
lst_head = lambda lst: lst[0]

# Return the node at the tail of lst, or None.
lst_tail = lambda lst: lst[1]

# Given some node or None, return the previous node or None.
lst_prev = lambda node: node[0] if node else None

# Given some node or None, return the next node or None.
lst_next = lambda node: node[2] if node else None

# Given some node or None, return the node value or None.
lst_value = lambda node, default=None: node[1] if node else default

# Given some node and value, replace the node's value with value.
lst_setvalue = lambda node, value: node.__setitem__(1, value)


def lst_unlink(lst, node):
    '''Unlink node from lst. Returns the unlinked node.'''
    if node[0]:                 # if node.prev:
        node[0][2] = node[2]    #   node.prev.next = node.next
    else:                       # (we're the head)
        lst[0] = node[2]        #   head = next
        if lst[0]:              #   if head:
            lst[0][0] = None    #       head.prev = None

    if node[2]:                 # if node.next:
        node[2][0] = node[0]    #   node.next.prev = node.prev
    else:                       # (we're the tail)
        lst[1] = node[0]        #   tail = node.prev
        if lst[1]:              #   if tail:
            lst[1][2] = None    #       tail.next = None
    return node


def lst_append(lst, obj):
    '''Create a new node containing obj and append it to lst. Return the new
    node.'''
    lst[1] = node = [lst[1], obj, None]
    if node[0]:
        node[0][2] = node
    if not lst[0]:
        lst[0] = node
    return node


def lst_movehead(lst, node):
    '''Move node to the start of lst.'''
    if node[0]:
        lst_unlink(lst, node)
        node[0] = None
        node[2] = lst[0]
        lst[0] = node
        if node[2]:
            node[2][0] = node


def lst_prepend(lst, obj):
    '''Create a new node containing obj and prepend it to lst. Return the new
    node.'''
    lst[0] = node = [None, obj, lst[0]]
    if node[2]:
        node[2][0] = node
    if not lst[1]:
        lst[1] = node
    return node


def lst_iter(node, values=False, reverse=False):
    '''Given a starting node, yield it or its value, doing the same for
    subsequent nodes going forward or in reverse.'''
    while node:
        yield node[1] if values else node
        node = node[0 if reverse else 2]


def slice_abs(sl, length):
    '''Convert the slice `sl' to a 2-tuple (start-offset, end-offset) of
    absolute offsets in relation to a sequence of length `length'.'''
    def dumb(val):
        return max(0, length + val) if val < 0 else min(length, val)

    return dumb(sl.start or 0), dumb(sl.stop or length)


class LruCache(object):
    '''Cache with LRU pruning. This uses a linked list to efficiently move
    items up the LRU list. There appears to be no built in way of doing this
    without using O(n) list/deque remove().

    Items form a doubly linked list; get() causes the item to be moved to the
    head, allowing the oldest item (the tail) to be discarded when put() on a
    full cache occurs.'''

    def __init__(self, size):
        self.size = size
        self.mapping = {}
        self.lst = lst_new()

    def get(self, key):
        node = self.mapping.get(key)
        if node:
            lst_movehead(self.lst, node)
            return lst_value(node)[1]

    def put(self, key, value):
        node = self.mapping.get(key)
        if node:
            lst_movehead(self.lst, node)
            lst_setvalue(node, (key, value))
            return

        if len(self.mapping) == self.size:
            node = lst_unlink(self.lst, lst_tail(self.lst))
            del self.mapping[lst_value(node)[0]]

        self.mapping[key] = lst_prepend(self.lst, (key, value))


class BaseMapping(object):
    def __init__(self, maxoff):
        self.maxoff = maxoff

    def __len__(self):
        return self.maxoff + 1

    def pread(self, off, length):
        raise NotImplementedError

    def __getitem__(self, i):
        assert isinstance(i, (slice, int, long))

        if type(i) is slice:
            start, stop = slice_abs(i, self.maxoff)
            s = self.pread(start, stop-start)
            if i.step:
                return s[::i.step]
            else:
                return s

        c = self[i:i+1]
        if not c:
            raise IndexError(i)
        return c


class FileMapping(BaseMapping):
    def __init__(self, fp):
        self.fp = fp
        fp.seek(0, 2)

        super(FileMapping, self).__init__(fp.tell())

    def pread(self, off, length):
        self.fp.seek(off)
        return self.fp.read(length)


class CachedMapping(BaseMapping):
    def __init__(self, maxoff, cache_size=1048576, page_size=16384):
        super(CachedMapping, self).__init__(maxoff)
        self.cache_size = cache_size
        self.page_size = page_size
        self.cache = LruCache(cache_size / page_size)


class PagedFileMapping(FileMapping):
    def __init__(self, fp, cache_size=1048576, page_size=16384):
        super(PagedFileMapping, self).__init__(fp)
        #self.cache_
        self.page_size = page_size

    def _get_page(self, i):
        page = self.cache.get(i)
        if not page:
            self.fp.seek(i * self.page_size)
            page = self.fp.read(self.page_size)
            self.cache.put(i, page)

        return page

    def pread(self, off, length):
        bits = []
        page, off = divmod(off, self.page_size)

        while length:
            s = self._get_page(page)[off:off+length]
            if not s:
                break
            length -= len(s)
            bits.append(s)
            off = 0
            page += 1

        return ''.join(bits)


class SegmentedFileMapping:
    pass

'''
pfm = PagedFileMapping(file('/etc/services'), page_size=4096)

s = pfm[:9]
print len(s)
print repr(s)
print pfm.cache
print len(pfm[:])
print len(pfm[::2])
print len(pfm[::8])
print len(pfm[::16])
'''

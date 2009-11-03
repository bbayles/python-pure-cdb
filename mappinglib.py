#!/usr/bin/env python2.5

import collections


def slice_abs(sl, length):
    def dumb(val):
        return max(0, length + val) if val < 0 else min(length, val)

    return dumb(sl.start or 0), dumb(sl.stop or length)


class FileMapping(object):
    def __init__(self, fp):
        self.fp = fp
        fp.seek(0, 2)
        self.maxoff = fp.tell()

    def __len__(self):
        return self.maxoff + 1

    def pread(self, off, length):
        self.fp.seek(off)
        return self.fp.read(length)

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


class PagedFileMapping(FileMapping):
    def __init__(self, fp, cache_size=1048576, page_size=16384):
        super(PagedFileMapping, self).__init__(fp)
        self.cache_size = cache_size
        self.page_size = page_size
        self.pages_max = cache_size / page_size
        self.cache = {}
        self.lru = collections.deque()

    def _get_page(self, i):
        page = self.cache.get(i)
        if page:
            self.lru.remove(i)
            self.lru.appendleft(i)
            return page

        self.fp.seek(i * self.page_size)
        page = self.fp.read(self.page_size)
        if len(self.lru) == self.pages_max:
            old_i = self.lru.pop()
            del self.cache[old_i]

        self.cache[i] = page
        self.lru.appendleft(i)
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


pfm = PagedFileMapping(file('/etc/passwd'), page_size=1)

s = pfm[:9]
print len(s)
print repr(s)
print pfm.cache
print len(pfm[:])
print len(pfm[::2])
print len(pfm[::8])
print len(pfm[::16])

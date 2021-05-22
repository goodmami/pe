
import re


DEF FAILURE = -1


cdef class Scanner:
    cpdef int scan(self, str s, int pos=0) except -2:
        try:
            return self._scan(s, pos, len(s))
        except IndexError:
            return FAILURE

    cdef int _scan(self, str s, int pos, int slen) except -2:
        return FAILURE


cdef class Dot(Scanner):
    cdef int _scan(self, str s, int pos, int slen) except -2:
        if pos < slen:
            return pos + 1
        return FAILURE


cdef class Literal(Scanner):

    def __init__(self, str x):
        self._x = x
        self._xlen = len(x)

    cdef int _scan(self, str s, int pos, int slen) except -2:
        cdef int end = pos + self._xlen
        if s[pos:end] != self._x:
            return FAILURE
        return end


cdef class CharacterClass(Scanner):

    def __init__(
        self,
        list ranges,
        bint negate = False,
        int mincount = 1,
        int maxcount = 1
    ):
        self._chars = ''.join(a for a, b in ranges if not b)
        self._ranges = ''.join(a+b for a, b in ranges if b)
        self._rangelen = len(self._ranges)
        self._negate = negate
        self.mincount = mincount
        self.maxcount = maxcount

    cdef int _scan(self, str s, int pos, int slen) except -2:
        cdef Py_UCS4 c
        cdef str ranges = self._ranges
        cdef bint matched
        cdef int mincount = self.mincount
        cdef int maxcount = self.maxcount
        cdef int i = 0
        while maxcount and pos < slen:
            c = s[pos]
            matched = False
            if c in self._chars:
                matched = True
            else:
                while i < self._rangelen:
                    if ranges[i] <= c <= ranges[i+1]:
                        matched = True
                        break
                    i += 2
            if matched ^ self._negate:
                pos += 1
                maxcount -= 1
                mincount -= 1
            else:
                break
        if mincount > 0:
            return FAILURE
        return pos


cdef class Regex(Scanner):
    def __init__(self, str pattern, int flags=0):
        self._regex = re.compile(pattern, flags=flags)

    cdef int _scan(self, str s, int pos, int slen) except -2:
        m = self._regex.match(s, pos=pos)
        if m is None:
            return FAILURE
        else:
            return m.end()

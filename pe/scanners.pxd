
cdef class Scanner:
    cpdef int scan(self, str s, int pos=*) except -2
    cdef int _scan(self, str s, int pos, int slen) except -2


cdef class Dot(Scanner):
    pass


cdef class Literal(Scanner):
    cdef str _x
    cdef int _xlen


cdef class CharacterClass(Scanner):
    cdef:
        str _chars, _ranges
        int _rangelen
        bint _negate
    cdef public:
        int mincount, maxcount


cdef class Regex(Scanner):
    cdef object _regex

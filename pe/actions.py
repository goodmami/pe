
def constant(value):

    def constant_value(*args, **kwargs):
        return value

    return constant_value


def pack(func):

    def call_func(*args, **kwargs):
        return func(args, **kwargs)

    return call_func


def raw(func):

    def call_func(*args, **kwargs):
        return func(''.join(args), **kwargs)

    return call_func


def first(*args, **kwargs):
    return args[0]


def last(*args, **kwargs):
    return args[-1]

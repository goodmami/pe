
def constant(value):

    def constant_value(*args, **kwargs):
        return value

    return constant_value


def first(*args, **kwargs):
    return args[0]


def last(*args, **kwargs):
    return args[-1]

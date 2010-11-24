# encoding: utf-8

"""Sample callables with varying syntax for testing purposes."""


import logging
from marrow.script import annotate, describe



def simple():
    "A simple function that takes no arguments."
    print "Hello world!"


def retval():
    "A simple function that takes no arguments and returns a status code of 1."
    print "Farewell cruel world!"
    return 1


def single(name):
    """A simple function with a single argument, no default value.
    
    Additionally, this has a long description."""
    logging.debug("name=%r", name)
    assert isinstance(name, str)
    print "Hello %s!" % (name, )


def default(name="world"):
    "A simple function with a single argument, string default value."
    logging.debug("name=%r", name)
    assert isinstance(name, str)
    
    print "Hello %s!" % (name, )
    
    return 0 if name == "world" else 1


def integer(value=0):
    "A simple function with a single argument, numeric default value."
    logging.debug("value=%r", value)
    assert isinstance(value, int)
    
    print "%d" % (value, )
    
    return value


def boolean(value=False):
    return 1 if value else 0


def lists(value=[]):
    return len(value)


@annotate(x=int, y=int)
def multiply(x, y):
    "A decorated function with two, non-defaulting arguments."
    logging.debug("x=%r y=%r", x, y)
    assert isinstance(x, int)
    assert isinstance(y, int)
    
    print "%d * %d = %d" % (x, y, x * y)
    return x * y


def args(*args):
    """A function that takes unlimited arguments."""
    logging.debug("args=%r", args)
    return len(args)


def kwargs(**kw):
    """A function that takes unlimited keyword arguments."""
    logging.debug("kw=%r", kw)
    return len(kw)

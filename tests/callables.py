# encoding: utf-8

"""Sample callables with varying syntax for testing purposes."""


from marrow.script import annotate, describe



def simple():
    "A simple function that takes no arguments."
    print "Hello world!"


def single(name):
    "A simple function with a single argument, no default value."
    print "Hello %s!" % (name, )


def default(name="world"):
    "A simple function with a single argument, string default value."
    print "Hello %s!" % (name, )


def integer(value=0):
    "A simple function with a single argument, numeric default value."
    print "%d" % (value, )


@annotate(x=int, y=int)
def multiply(x, y):
    "A decorated function with two, non-defaulting arguments."
    print "%d * %d = %d" % (x, y, x * y)

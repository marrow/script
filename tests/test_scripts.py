# encoding: utf-8

from __future__ import print_function

import logging

from pprint import pformat
from unittest import TestCase

from marrow.util.compat import IO, unicode

from marrow.script.core import *

from marrow.script import annotate, describe



def simple():
    "A simple function that takes no arguments."
    print("Hello world!")


def retval():
    "A simple function that takes no arguments and returns a status code of 1."
    print("Farewell cruel world!")
    return 1


def single(name):
    """A simple function with a single argument, no default value.
    
    Additionally, this has a long description."""
    logging.debug("name=%r", name)
    assert isinstance(name, str)
    print("Hello "+name+"%s!")


def default(name="world"):
    "A simple function with a single argument, string default value."
    logging.debug("name=%r", name)
    assert isinstance(name, str)
    
    print("Hello "+name+"!")
    
    return 0 if name == "world" else 1


def integer(value=0):
    "A simple function with a single argument, numeric default value."
    logging.debug("value=%r", value)
    assert isinstance(value, int)
    
    print(value)
    
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
    
    print(x, '*', y, '=', x * y)
    return x * y


def args(*args):
    """A function that takes unlimited arguments."""
    logging.debug("args=%r", args)
    return len(args)


def kwargs(**kw):
    """A function that takes unlimited keyword arguments."""
    logging.debug("kw=%r", kw)
    return len(kw)




class TestCore(TestCase):
    def test_simple(self):
        _ = Parser(simple)()
        self.assertEquals(_, None)
        
        _ = Parser(simple)(['-h'])
        self.assertEquals(_, 64)
        
        _ = Parser(simple)(['--help'])
        self.assertEquals(_, 64)
        
        _ = Parser(simple)(['-V'])
        self.assertEquals(_, 64)
        
        _ = Parser(simple)(['--version'])
        self.assertEquals(_, 64)
    
    def test_retval(self):
        _ = Parser(retval)()
        self.assertEquals(_, 1)
    
    def test_single(self):
        _ = Parser(single)(["world"])
        self.assertEquals(_, None)
        
        _ = Parser(single)(["--", "--world"])
        self.assertEquals(_, None)
    
    def test_single_error(self):
        _ = Parser(single)()
        self.assertEquals(_, 64)
    
    def test_default(self):
        _ = Parser(default)()
        self.assertEquals(_, 0)
        
        _ = Parser(default)(['father'])
        self.assertEquals(_, 64)
        
        _ = Parser(default)(['--name=father'])
        self.assertEquals(_, 1)
        
        _ = Parser(default)(['--name', 'father'])
        self.assertEquals(_, 1)
    
    def test_integer(self):
        _ = Parser(integer)()
        self.assertEquals(_, 0)
        
        _ = Parser(integer)(['--value=1'])
        self.assertEquals(_, 1)
        
        _ = Parser(integer)(['--value=a'])
        self.assertEquals(_, 64)
    
    def test_boolean(self):
        _ = Parser(boolean)()
        self.assertEquals(_, 0)
        
        _ = Parser(boolean)(['--value'])
        self.assertEquals(_, 1)
        
        _ = Parser(boolean)(['-v'])
        self.assertEquals(_, 1)
        
        _ = Parser(boolean)(['-v', '-v'])
        self.assertEquals(_, 64)
        
        _ = Parser(boolean)(['a'])
        self.assertEquals(_, 64)
    
    def test_lists(self):
        _ = Parser(lists)()
        self.assertEquals(_, 0)
        
        _ = Parser(lists)(['--value', '1'])
        self.assertEquals(_, 1)
        
        _ = Parser(lists)(['--value=1,2,3'])
        self.assertEquals(_, 3)
    
    def test_multiply(self):
        _ = Parser(multiply)()
        self.assertEquals(_, 64)
        
        _ = Parser(multiply)(['2'])
        self.assertEquals(_, 64)
        
        _ = Parser(multiply)(['2', '4'])
        self.assertEquals(_, 8)
    
    def test_args(self):
        _ = Parser(args)()
        self.assertEquals(_, 0)
        
        _ = Parser(args)(['--help'])
        self.assertEquals(_, 64)
        
        _ = Parser(args)(['value'])
        self.assertEquals(_, 1)
        
        _ = Parser(args)(['value', 'value'])
        self.assertEquals(_, 2)
        
        _ = Parser(args)(['--', '--value'])
        self.assertEquals(_, 1)
    
    def test_kwargs(self):
        _ = Parser(kwargs)()
        self.assertEquals(_, 0)
        
        _ = Parser(kwargs)(['--help'])
        self.assertEquals(_, 64)
        
        _ = Parser(kwargs)(['--name=value'])
        self.assertEquals(_, 1)
    
    def test_core_callbacks(self):
        def myhelp(obj, spec):
            return -1
        
        def myver(obj, spec):
            return -2
        
        _ = Parser(simple, help=myhelp)(['--help'])
        self.assertEquals(_, -1)
        
        _ = Parser(simple, version=myver)(['--version'])
        self.assertEquals(_, -2)
    
    def test_class(self):
        class Foo(object):
            pass
        
        self.assertRaises(NotImplementedError, lambda: Parser(Foo)())
    

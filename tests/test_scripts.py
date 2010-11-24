# encoding: utf-8

from pprint import pformat
from unittest import TestCase

from marrow.util.compat import IO, unicode

from marrow.script.core import *
import callables



class TestCore(TestCase):
    def test_simple(self):
        _ = Parser(callables.simple)()
        self.assertEquals(_, None)
        
        _ = Parser(callables.simple)(['-h'])
        self.assertEquals(_, 64)
        
        _ = Parser(callables.simple)(['--help'])
        self.assertEquals(_, 64)
        
        _ = Parser(callables.simple)(['-V'])
        self.assertEquals(_, 64)
        
        _ = Parser(callables.simple)(['--version'])
        self.assertEquals(_, 64)
    
    def test_retval(self):
        _ = Parser(callables.retval)()
        self.assertEquals(_, 1)
    
    def test_single(self):
        _ = Parser(callables.single)(["world"])
        self.assertEquals(_, None)
        
        _ = Parser(callables.single)(["--", "--world"])
        self.assertEquals(_, None)
    
    def test_single_error(self):
        _ = Parser(callables.single)()
        self.assertEquals(_, 64)
    
    def test_default(self):
        _ = Parser(callables.default)()
        self.assertEquals(_, 0)
        
        _ = Parser(callables.default)(['father'])
        self.assertEquals(_, 64)
        
        _ = Parser(callables.default)(['--name=father'])
        self.assertEquals(_, 1)
        
        _ = Parser(callables.default)(['--name', 'father'])
        self.assertEquals(_, 1)
    
    def test_integer(self):
        _ = Parser(callables.integer)()
        self.assertEquals(_, 0)
        
        _ = Parser(callables.integer)(['--value=1'])
        self.assertEquals(_, 1)
        
        _ = Parser(callables.integer)(['--value=a'])
        self.assertEquals(_, 64)
    
    def test_boolean(self):
        _ = Parser(callables.boolean)()
        self.assertEquals(_, 0)
        
        _ = Parser(callables.boolean)(['--value'])
        self.assertEquals(_, 1)
        
        _ = Parser(callables.boolean)(['-v'])
        self.assertEquals(_, 1)
        
        _ = Parser(callables.boolean)(['-v', '-v'])
        self.assertEquals(_, 64)
        
        _ = Parser(callables.boolean)(['a'])
        self.assertEquals(_, 64)
    
    def test_lists(self):
        _ = Parser(callables.lists)()
        self.assertEquals(_, 0)
        
        _ = Parser(callables.lists)(['--value', '1'])
        self.assertEquals(_, 1)
        
        _ = Parser(callables.lists)(['--value=1,2,3'])
        self.assertEquals(_, 3)
    
    def test_multiply(self):
        _ = Parser(callables.multiply)()
        self.assertEquals(_, 64)
        
        _ = Parser(callables.multiply)(['2'])
        self.assertEquals(_, 64)
        
        _ = Parser(callables.multiply)(['2', '4'])
        self.assertEquals(_, 8)
    
    def test_args(self):
        _ = Parser(callables.args)()
        self.assertEquals(_, 0)
        
        _ = Parser(callables.args)(['--help'])
        self.assertEquals(_, 64)
        
        _ = Parser(callables.args)(['value'])
        self.assertEquals(_, 1)
        
        _ = Parser(callables.args)(['value', 'value'])
        self.assertEquals(_, 2)
        
        _ = Parser(callables.args)(['--', '--value'])
        self.assertEquals(_, 1)
    
    def test_kwargs(self):
        _ = Parser(callables.kwargs)()
        self.assertEquals(_, 0)
        
        _ = Parser(callables.kwargs)(['--help'])
        self.assertEquals(_, 64)
        
        _ = Parser(callables.kwargs)(['--name=value'])
        self.assertEquals(_, 1)
    
    def test_core_callbacks(self):
        def myhelp(obj, spec):
            return -1
        
        def myver(obj, spec):
            return -2
        
        _ = Parser(callables.simple, help=myhelp)(['--help'])
        self.assertEquals(_, -1)
        
        _ = Parser(callables.simple, version=myver)(['--version'])
        self.assertEquals(_, -2)
    
    def test_class(self):
        class Foo(object):
            pass
        
        self.assertRaises(NotImplementedError, lambda: Parser(Foo)())
    

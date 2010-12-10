# encoding: utf-8

from __future__ import unicode_literals
from __future__ import print_function

import logging

from pprint import pformat
from unittest import TestCase

from marrow.util.compat import IO, unicode

from marrow.script.core import *

from marrow.script import script, annotate, describe



class Foo(object):
    def bar(self):
        pass
    
    def baz(self):
        return 1


class Bar(object):
    def __init__(self, argument):
        self.argument = argument
    
    def foo(self):
        return len(self.argument)
    
    def baz(self, argument):
        return len(self.argument) + len(argument)



class TestClasses(TestCase):
    def test_foo_noargs(self):
        _ = Parser(Foo)()
        self.assertEquals(_, 64)
    
    def test_foo_bar(self):
        _ = Parser(Foo)(["bar"])
        self.assertEquals(_, 0)
    
    def test_foo_baz(self):
        _ = Parser(Foo)(["baz"])
        self.assertEquals(_, 1)
    
    def test_bar_arg(self):
        _ = Parser(Bar)()
        self.assertEquals(_, 64)
        
        _ = Parser(Bar)(["world"])
        self.assertEquals(_, 64)
    
    def test_bar_foo(self):
        _ = Parser(Bar)(["world", "foo"])
        self.assertEquals(_, 5)
    
    def test_bar_baz(self):
        _ = Parser(Bar)(["world", "baz", "hello"])
        self.assertEquals(_, 10)

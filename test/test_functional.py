# encoding: utf-8

from __future__ import unicode_literals, print_function

from unittest import TestCase

from marrow.script.core import Parser
from marrow.script import script, annotate

from helper import capture


class TestFunctionalInterface(TestCase):
	def test__example__called_with_explicit_help(self):
		@script(title="Simple", version="1.0")
		def example__no_arguments(): pass
		
		assert Parser(example__no_arguments)(['--help']) == 64
		assert Parser(example__no_arguments)(['-h']) == 64
	
	def test__example__called_with_explicit_version(self):
		@script(title="Simple", version="1.0")
		def example__no_arguments(): pass
		
		assert Parser(example__no_arguments)(['--version']) == 64
		assert Parser(example__no_arguments)(['-V']) == 64
	
	def test__example__returning_nonzero(self):
		def example__no_arguments__nonzero():
			return 1
		
		assert Parser(example__no_arguments__nonzero)() == 1
	
	def test__example__with_no_arguments(self):
		def example__no_arguments():
			example__no_arguments.run = True
			return 0
		
		example__no_arguments.run = False
		
		assert Parser(example__no_arguments)() == 0
		assert example__no_arguments.run
	
	def test__example__with_required_arguments_missing(self):
		def example__positional_arguments(name):
			print("Hello", name)
		
		with capture() as stdout:
			assert Parser(example__positional_arguments)() == 64
			result = stdout.getvalue()
		
		assert 'name' in result
	
	def test__example__with_required_arguments_provided(self):
		def example__positional_arguments(name):
			print("Hello", name)
		
		with capture() as stdout:
			assert Parser(example__positional_arguments)(['world']) == 0
			result = stdout.getvalue()
		
		assert 'Hello' in result
		assert 'world' in result
	
	def test__example__with_required_arguments_provided_after_arglist_terminator(self):
		def example__positional_arguments(name):
			print("Hello", name)
		
		with capture() as stdout:
			assert Parser(example__positional_arguments)(["--", "--world"]) == 0
			result = stdout.getvalue()
		
		assert '--world' in result
	
	def test__default__arguments_example(self):
		def default(name="world"):
			print("Hello " + name + "!")
			return 0 if name == "world" else 1
		
		assert Parser(default)() == 0
		assert Parser(default)(['--name=father']) == 1
		assert Parser(default)(['--name', 'father']) == 1
	
	def test__integer__casting_example(self):
		def integer(value=0):
			assert isinstance(value, int)
			print(value)
			return value
		
		assert Parser(integer)() == 0
		assert Parser(integer)(['--value=1']) == 1
		assert Parser(integer)(['--value=a']) == 64
	
	def test__boolean__casting_example(self):
		def boolean(value=False):
			return 1 if value else 0
		
		assert Parser(boolean)() == 0
		assert Parser(boolean)(['--value']) == 1
		assert Parser(boolean)(['-v']) == 1
		assert Parser(boolean)(['a']) == 64
		
		# Repeated boolean values = single boolean value
		assert Parser(boolean)(['-v', '-v']) == 1
	
	def test__lists__processing_example(self):
		def lists(value=[]):
			return len(value)
		
		assert Parser(lists)() == 0
		assert Parser(lists)(['--value', '1']) == 1
		assert Parser(lists)(['--value=1,2,3']) == 3
	
	def test__multiply__processing_example(self):
		@annotate(x=int, y=int)
		def multiply(x, y):
			x, y = int(x), int(y)
			
			assert isinstance(x, int)
			assert isinstance(y, int)
			
			print(x, '*', y, '=', x * y)
			return x * y
		
		assert Parser(multiply)() == 64
		assert Parser(multiply)(['2']) == 64
		assert Parser(multiply)(['2', '4']) == 8
	
	def test__args__unlimited_argument_list(self):
		def args(*args):
			return len(args)
		
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
		def kwargs(**kw):
			return len(kw)
		
		_ = Parser(kwargs)()
		self.assertEquals(_, 0)
		
		_ = Parser(kwargs)(['--help'])
		self.assertEquals(_, 64)
		
		_ = Parser(kwargs)(['--name=value'])
		self.assertEquals(_, 1)
		
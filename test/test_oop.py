# encoding: utf-8

from __future__ import unicode_literals


from unittest import TestCase

from marrow.script.core import Parser

from helper import capture


class TestSimpleCommandInterface(TestCase):
	class ExampleNoInit(object):
		def success(self):
			return 0
		
		def fail(self):
			return 1
	
	def test__example__called_without_command(self):
		with capture() as stdout:
			assert Parser(self.ExampleNoInit)() == 64
			
			result = stdout.getvalue()
		
		assert 'success' in result
		assert 'fail' in result
	
	def test__example__executes_success(self):
		assert Parser(self.ExampleNoInit)(['success']) == 0
	
	def test__example__executes_fail(self):
		assert Parser(self.ExampleNoInit)(['fail']) == 1

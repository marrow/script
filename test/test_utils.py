# encoding: utf-8

from pprint import pformat
from unittest import TestCase

from marrow.script.util import wrap, getargspec


wrap_source = "Lorem ipsum dolor sit amet, consectetur adipisicing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat. Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur. Excepteur sint occaecat cupidatat non proident, sunt in culpa qui officia deserunt mollit anim id est laborum."

class TestUtilities(TestCase):
	def test_wrapping_basic(self):
		assert wrap(wrap_source) == 'Lorem ipsum dolor sit amet, consectetur adipisicing elit, sed do eiusmod\ntempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam,\nquis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo\nconsequat. Duis aute irure dolor in reprehenderit in voluptate velit esse\ncillum dolore eu fugiat nulla pariatur. Excepteur sint occaecat cupidatat non\nproident, sunt in culpa qui officia deserunt mollit anim id est laborum.'
		
		assert wrap(wrap_source, 100) == 'Lorem ipsum dolor sit amet, consectetur adipisicing elit, sed do eiusmod tempor incididunt ut labore\net dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut\naliquip ex ea commodo consequat. Duis aute irure dolor in reprehenderit in voluptate velit esse\ncillum dolore eu fugiat nulla pariatur. Excepteur sint occaecat cupidatat non proident, sunt in\nculpa qui officia deserunt mollit anim id est laborum.'
		
		assert wrap(wrap_source, 1000) == wrap_source
	
	def test_wrapping_list(self):
		assert wrap(['a', 'b', 'c']) == 'a b c'
		assert wrap(['a', '', 'c']) == 'a\n\nc'
		
		assert wrap([wrap_source, '', 'c']) == 'Lorem ipsum dolor sit amet, consectetur adipisicing elit, sed do eiusmod\ntempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam,\nquis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo\nconsequat. Duis aute irure dolor in reprehenderit in voluptate velit esse\ncillum dolore eu fugiat nulla pariatur. Excepteur sint occaecat cupidatat non\nproident, sunt in culpa qui officia deserunt mollit anim id est laborum.\n\nc'
	
	def test_argspec_fail(self):
		self.assertRaises(TypeError, lambda: getargspec(wrap_source))
	
	def test_argspec_basic(self):
		assert pformat(getargspec(self.test_wrapping_basic)) == '([], {}, False, False)'
	
	def test_argspec_args(self):
		def foo(arg1, arg2, *args):
			pass
		
		assert pformat(getargspec(foo)) == "(['arg1', 'arg2'], {}, True, False)"
	
	def test_argspec_kwargs(self):
		def foo(arg1=None, arg2=None, **kw):
			pass
		
		assert pformat(getargspec(foo)) == "(['arg1', 'arg2'], {'arg1': None, 'arg2': None}, False, True)"
	
	def test_class_inspect(self):
		class Foo(object):
			def foo(self):
				pass
		
		assert pformat(getargspec(Foo)) == '([], {}, False, False)'
		assert pformat(getargspec(Foo.foo)) == '([], {}, False, False)'
		assert pformat(getargspec(Foo().foo)) == '([], {}, False, False)'

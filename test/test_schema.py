# encoding: utf-8

from unittest import TestCase

from marrow.script.schema import Specification


class TestSpecification(TestCase):
	def test_unresolvable_specification_raises(self):
		try:
			Specification.from_object(None)
		except TypeError:
			pass
		else:
			assert False, "Failed to raise TypeError."
	
	def test__basic_function__specification(self):
		def basic_function(name, severity='!'):
			return "Hello " + name + severity
		
		spec = Specification.from_object(basic_function)
		
		assert len(spec.__arguments__) == 2
		assert tuple(spec.__arguments__) == ('name', 'severity')
		assert spec._vargs == spec._kwargs == False
		assert spec.name.short is None
		assert spec.severity.short == 's'
	
	def test__basic_class__initializer_specification(self):
		class BasicClass(object):
			def __init__(self):
				pass
		
		spec = Specification.from_object(BasicClass)
		
		assert len(spec.__arguments__) == 0
	
	def test_conflicting_abbreviations(self):
		def basic_conflicting(bar=1, baz=2, biz=3): pass
		
		spec = Specification.from_object(basic_conflicting)
		
		assert len(spec.__arguments__) == 3
		assert tuple(i.short for i in spec.__arguments__.values()) == ('b', 'B', 'i')
	
	def test_specification_caching_behaviour(self):
		def basic_function(): pass
		
		spec1 = Specification.from_object(basic_function)
		spec2 = Specification.from_object(basic_function)
		
		assert spec1 is spec2
	
	def test_specification_application(self):
		def basic_function(name, severity='!'):
			return "Hello " + name + severity
		
		Spec = Specification.from_object(basic_function)
		
		spec = Spec()
		spec.name = "Bob Dole"
		
		print(spec.__data__)
		args, kwargs = spec.apply()
		
		assert args == ("Bob Dole", )
		assert kwargs == dict(severity='!')
		

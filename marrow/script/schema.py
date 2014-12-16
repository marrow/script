# encoding: utf-8

from __future__ import unicode_literals, print_function

from collections import namedtuple
from inspect import isclass, isfunction, getdoc, getmembers
from textwrap import dedent

from marrow.schema import Container, DataAttribute, Attribute, CallbackAttribute, Attributes
from marrow.schema.meta import ElementMeta
from marrow.schema.validate import always, Validated
from marrow.schema.transform import Transform, array, boolean, integer, decimal, number

from .exc import ExitException, ScriptError, MalformedArguments
from .util import wrap, partitionhelp


context = namedtuple("context", ('attribute', 'container'))




class Argument(Attribute):
	short = Attribute(default=None)
	description = Attribute(default=None)
	transform = CallbackAttribute(default=Transform())
	validator = CallbackAttribute(default=always)
	
	def __set__(self, obj, value):
		ctx = context(self, obj)
		
		value = self.transform.native(value, ctx)
		value = self.validator.validate(value, ctx)
		
		super(Argument, self).__set__(obj, value)


class SwitchTransform(Transform):
	def native(self, value, context):
		if hasattr(value, 'lower'):
			value = value.lower()
		
		if value in (True, 'yes', 'y', 'true', 't', 'on'):
			return context.attribute.truthy
		
		return context.attribute.falsy


class Switch(Argument):
	transform = CallbackAttribute(default=SwitchTransform())
	truthy = CallbackAttribute(default=True)
	falsy = CallbackAttribute(default=False)


class Command(Attribute):
	description = Attribute(default=None)
	epilog = Attribute(default=None)
	parent = Attribute(default=None)
	specification = Attribute()
	target = Attribute()
	
	@classmethod
	def from_object(cls, target, **kw):
		if not ( isclass(target) or isfunction(target) ):
			raise TypeError("Invalid target for command-line script: " + repr(obj))
		
		if hasattr(target, '__script_command__'):
			target.__script_command__.parent = kw.get('parent', None)
			return target.__script_command__
		
		if 'description' not in kw:
			kw['description'] = getdoc(target)
		
		if 'specification' not in kw:
			kw['specification'] = Specification.from_object(target, kw.get('parent', None))
		
		self = cls(target=target, **kw)
		
		try:
			target.__script_command__ = self
		except:
			pass
		
		return self


class Specification(Attribute):
	__arguments__ = Attributes(Argument)
	__commands__ = Attributes(Command)
	_vargs = Attribute(default=False)
	_kwargs = Attribute(default=False)
	
	@classmethod
	def from_object(cls, obj, parent=None):
		# We construct a new Specification subclass dedicated to this function.
		# It's gettin' weird, Jerry.
		
		# If we have no hope, bail early.
		if not callable(obj):
			raise TypeError("Invalid target for spcification: " + repr(obj))
		
		# An existing class is a handy shortcut.
		if hasattr(obj, '__script_spec_class__'):
			return obj.__script_spec_class__
		
		parts = dict()
		
		# Inspect and populate a new schema for this callable.
		args, vargs, kwargs, defaults = getargspec(obj)
		
		# Construct the final class.
		spec = ElementMeta("Specification_" + obj.__name__, (Specification, ), parts)
		
		# Cache if possible.
		try:
			obj.__script_spec_class__ = spec
		except:
			pass
		
		return spec
	

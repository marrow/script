# encoding: utf-8

from __future__ import unicode_literals, print_function

from collections import namedtuple
from inspect import isclass, isfunction, ismethod, getdoc, getmembers
from textwrap import dedent

from marrow.schema import Container, DataAttribute, Attribute, CallbackAttribute, Attributes
from marrow.schema.meta import ElementMeta
from marrow.schema.validate import always, Validated
from marrow.schema.transform import Transform, array, boolean, integer, decimal, number

from .exc import ExitException, ScriptError, MalformedArguments
from .util import wrap, partitionhelp, getargspec


context = namedtuple("context", ('attribute', 'container'))
nodefault = object()


class Argument(Attribute):
	default = Attribute(default=nodefault)
	short = Attribute(default=None)
	description = Attribute(default=None)
	transform = CallbackAttribute(default=Transform())
	validator = CallbackAttribute(default=always)
	
	def __repr__(self):
		return "{0.__class__.__name__}({1}{0.__name__}{2})".format(
				self,
				(self.short + ':') if self.short else '',
				', required' if self.default is nodefault else ''
			)
	
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
	
	def apply(self):
		"""Return a 2-tuple of (args, kw) in preparation for execution using these arguments."""
		
		seen = set()
		positional = []
		keyword = {}
		
		for arg, spec in self.__arguments__.items():
			if spec.default is nodefault:
				if arg == self._vargs:
					continue  # TEST: vargs
				
				positional.append(getattr(self, arg))
				seen.add(arg)
				continue
			
			if arg == self._kwargs:
				continue  # TEST: kwargs
			
			keyword[arg] = getattr(self, arg)
			seen.add(arg)
		
		if self._vargs:  # TEST: vargs
			positional.extend(getattr(self, self._vargs))
		
		if self._kwargs:  # TEST: kwargs
			# TODO: Identify redefinition and explode.
			keyword.update(getattr(self, self._kwargs))
		
		return tuple(positional), keyword
	
	@classmethod
	def from_object(cls, obj, parent=None):
		"""Construct a new Specification subclass dedicated to this function."""
		
		# It's gettin' weird, Jerry.
		
		# If we have no hope, bail early.
		if not callable(obj):
			raise TypeError("Invalid target for spcification: " + repr(obj))
		
		# An existing class is a handy shortcut.
		if hasattr(obj, '__script_spec_class__'):
			return obj.__script_spec_class__
		
		parts = dict()
		shorts = set()
		
		# Inspect and populate a new schema for this callable.
		
		args, defaults, parts['_vargs'], parts['_kwargs'] = getargspec(obj)
		annotations = getattr(obj, '__annotations__', {})
		
		for arg in args:
			argument = None
			arg_cls = Switch if isinstance(defaults.get(arg, None), bool) else Argument
			parts[arg] = arg_cls(arg)
			
			if arg in annotations:  # TEST
				ann = annotations[arg]
				
				if isinstance(ann, Argument):
					argument = ann
				
				elif callable(ann):
					pass  # TODO: Typecasting
				
				else:
					parts[arg] = ann
			
			if arg in defaults:
				# Default means optional, which means a switch.
				parts[arg].default = defaults[arg]
				
				# Determine acceptable (unique) short code.
				for c_ in arg:
					for c in (c_.lower(), c_.upper()):
						if c in shorts: continue
						parts[arg].short = c
						shorts.add(c)
						break
					else:
						continue
					break
		
		if parts['_vargs']:  # TEST: vargs
			parts[parts['_vargs']] = Argument(parts['_vargs'], default=tuple)
		
		if parts['_kwargs']:  # TEST: kwargs
			parts[parts['_kwargs']] = Argument(parts['_kwargs'], default=dict)
		
		# Construct the final class.
		spec = ElementMeta("Specification_" + obj.__name__, (Specification, ), parts)
		
		# Cache if possible.
		obj.__script_spec_class__ = spec
		
		return spec

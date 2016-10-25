# encoding: utf-8

from __future__ import unicode_literals, print_function

from collections import namedtuple
from inspect import isclass, isfunction, ismethod, getdoc

from marrow.schema import Attribute, CallbackAttribute, Attributes
from marrow.schema.meta import ElementMeta
from marrow.schema.validate import always
from marrow.schema.transform import Transform, IngressTransform

from .compat import signature, Parameter


context = namedtuple("context", ('attribute', 'container'))
nodefault = object()


class Argument(Attribute):
	default = Attribute(default=nodefault)
	short = Attribute(default=None)
	description = Attribute(default=None)
	transform = CallbackAttribute(default=Transform())
	validator = CallbackAttribute(default=always)
	
	@classmethod
	def from_inspect(cls, arg, reserved=None):
		"""Create a new instance from an `inspect.Argument` as provided by `inspect.signature`.
		
		To automatically calculate the argument abbreviation pass in a set of existing abbreviations as `reserved`.
		"""
		
		if arg.kind is Parameter.VAR_POSITIONAL:  # Handle the `*args` construct.
			return cls(arg.name, default=tuple)
		
		if arg.kind is Parameter.VAR_KEYWORD:  # Handle the `**kwargs` construct.
			return cls(arg.name, default=dict)
		
		if isinstance(arg.annotation, Argument):  # Explicit Argument annotation makes life easy.
			return arg.annotation
		
		cast = False
		argument = cls(arg.name)
		
		if arg.annotation is not Parameter.empty:
			if callable(arg.annotation):
				argument.transform = IngressTransform(arg.annotation)
				cast = True
			
			elif isinstance(arg.annotation, str):
				argument.description = arg.annotation
			
			elif isinstance(arg.annotation, tuple):
				argument.transform = IngressTransform(arg.annotation[0])
				argument.description = arg.annotation[1]
				cast = True
			
			else:
				raise TypeError("Invalid annotation for argument: " + arg.name)
		
		if arg.default is not Parameter.empty:
			if not cast and arg.default is not None:  # Simple inference given no explicit typecast callback.
				argument.transform = IngressTransform(type(arg.default))  # XXX: We might want a registry?
			
			argument.default = arg.default
		
		# Determine acceptable (unique) short code.
		if reserved:
			for char in arg.name:
				for letter in (char.lower(), char.upper()):
					if letter in reserved: continue
					argument.short = letter
					reserved.add(letter)
					return argument
		
		return argument
	
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
			raise TypeError("Invalid target for command-line script: " + repr(target))
		
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
		
		sig = signature(obj)
		
		for arg in sig.parameters:
			if arg.kind is Parameter.VAR_POSITIONAL:  # Handle the `*args` construct.
				parts['_vargs'] = arg.name
			
			elif arg.kind is Parameter.VAR_KEYWORD:  # Handle the `**kwargs` construct.
				parts['_kwargs'] = arg.name
			
			arg_cls = Switch if arg.annotation is bool or isinstance(arg.default, bool) else Argument
			parts[arg.name] = arg_cls.from_inspect(arg, reserved=shorts)
		
		# Construct the final class.
		spec = ElementMeta(obj.__name__.title() + "Specification", (Specification, ), parts)
		
		# Cache if possible.
		obj.__script_spec_class__ = spec
		
		return spec

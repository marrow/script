# encoding: utf-8

from __future__ import unicode_literals, print_function

try:
	from urllib.parser import urlparse
except ImportError:
	from urlparse import urlparse

from marrow.script import Script


def count(value):
	value = int(value)
	
	if value < 0 or value % 2:
		raise TypeError("Should be a positive, even integer.")
	
	return value


def url(value):
	if not isinstance(value, tuple):
		value = urlparse(value)
		
		if value.scheme not in ('http', 'https'):
			raise ValueError("Invalid URL scheme ({}). Only HTTP URLs are allowed.".format(value.scheme))
	
	return value


def validation(
			count: (count, "A positive, even number.") = 2,
			foo: "A mysterious parameter." = None,
			url: (url, "A URL") = None
		):
	"""Validation example.
	
	Performs validation using custom callbacks and inline checks.
	"""
	
	if foo is not None and foo != 'wat':
		raise ValueError("If a value is provided it must be the value 'wat'.")
	
	print("count:", count)
	print("foo:", foo)
	print("url:", url)


if __name__ == '__main__':
	Script.from_object(validation).run()

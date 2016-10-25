# encoding: utf-8

from __future__ import unicode_literals

import sys
import types
import inspect

from textwrap import wrap as wrap_


__all__ = ['wrap', 'InspectionComplete', 'InspectionFailed', 'getargspec', 'partitionhelp']


# Mac OS X terminal lies, so do others, probably.
# TODO: Needs testing; works on OS X.
encoding = sys.getdefaultencoding() if sys.getdefaultencoding() != 'ascii' else 'utf8'


def wrap(text, columns=78):
	lines = []
	
	if isinstance(text, list):
		in_paragraph = False
		for line in text:
			if not line:
				in_paragraph = False
				lines.append(line)
				continue
			
			if in_paragraph:
				lines[-1] = lines[-1] + ' ' + line
				continue
			
			lines.append(line)
			in_paragraph = True
		
		text = "\n".join(lines)
		lines = []
	
	in_paragraph = True
	for iline in text.splitlines():
		if not iline:
			lines.append(iline)
		else:
			for oline in wrap_(iline, columns):
				lines.append(oline)
	
	return "\n".join(lines)


class InspectionComplete(Exception):
	pass


class InspectionFailed(Exception):
	pass


def partitionhelp(s):
	if s is None: return "", ""
	
	head = []
	tail = []
	_ = head
	
	for line in [i.strip() for i in s.splitlines()]:
		if not line and _ is head:
			_ = tail
			continue
		
		_.append(line)
	
	return head, tail

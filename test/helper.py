# encoding: utf-8

from __future__ import unicode_literals

import sys

from contextlib import contextmanager
from tempfile import TemporaryFile

try:
	from io import StringIO
except ImportError:
	from cStringIO import StringIO


@contextmanager
def capture():
	old_stdout = sys.stdout
	with StringIO() as tmp:
		sys.stdout = tmp
		try:
			yield tmp
		finally:
			sys.stdout = old_stdout

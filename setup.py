#!/usr/bin/env python
# encoding: utf-8

from __future__ import print_function

import os
import sys
import codecs


try:
	from setuptools.core import setup, find_packages
except ImportError:
	from setuptools import setup, find_packages


if sys.version_info < (2, 7):
	raise SystemExit("Python 2.7 or later is required.")
elif sys.version_info > (3, 0) and sys.version_info < (3, 2):
	raise SystemExit("CPython 3.3 or Pypy 3 (3.2) or later is required.")

version = description = url = author = author_email = ""  # Silence linter warnings.
exec(open(os.path.join("marrow", "script", "release.py")).read())  # Actually populate those values.

here = os.path.abspath(os.path.dirname(__file__))

tests_require = [
		'pytest',  # test collector and extensible runner
		'pytest-cov',  # coverage reporting
		'pytest-flakes',  # syntax validation
		'pytest-capturelog',  # log capture
	]


setup(
	name = "marrow.script",
	version = version,
	description = description,
	long_description = codecs.open(os.path.join(here, 'README.rst'), 'r', 'utf8').read(),
	url = url,
	download_url = 'https://github.com/marrow/marrow.script/releases',
	author = author.name,
	author_email = author.email,
	license = 'MIT',
	keywords = ['marrow', 'cli', 'command line', 'scripting'],
	classifiers = [
			"Development Status :: 5 - Production/Stable",
			"Environment :: Console",
			"Intended Audience :: Developers",
			"License :: OSI Approved :: MIT License",
			"Operating System :: OS Independent",
			"Programming Language :: Python",
			"Programming Language :: Python :: 2",
			"Programming Language :: Python :: 2.7",
			"Programming Language :: Python :: 3",
			"Programming Language :: Python :: 3.2",
			"Programming Language :: Python :: 3.3",
			"Programming Language :: Python :: 3.4",
			"Programming Language :: Python :: 3.5",
			"Programming Language :: Python :: Implementation :: CPython",
			"Programming Language :: Python :: Implementation :: PyPy",
			"Topic :: Internet :: WWW/HTTP :: Dynamic Content",
			"Topic :: Internet :: WWW/HTTP :: WSGI",
			"Topic :: Software Development :: Libraries",
			"Topic :: Software Development :: Libraries :: Python Modules",
			"Topic :: Utilities",
		],
	
	packages = find_packages(exclude=['bench', 'docs', 'example', 'test', 'htmlcov']),
	include_package_data = True,
	package_data = {'': ['README.rst', 'LICENSE.txt']},
	namespace_packages = [
			'marrow',  # primary namespace
		],
	zip_safe = True,
	
	entry_points = {
		},
	
	setup_requires = [
			'pytest-runner',
		] if {'pytest', 'test', 'ptr'}.intersection(sys.argv) else [],
	install_requires = [
			'marrow.schema<2.0',  # dynamic execution and plugin management
			'funcsigs; python_version < "3.3"',  # Omni-port of PEP 362 (from Python 3.3's inspect module).
			'pathlib2; python_version < "3.4"',  # Path manipulation utility lib; builtin in 3.4 and 3.5.
		],
	tests_require = tests_require,
	extras_require = {
			'development': tests_require + [  # An extended set of useful development tools.
					'pre-commit',  # Git hook provider.
				],
		},
)

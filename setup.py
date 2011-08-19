#!/usr/bin/env python
# encoding: utf-8

import os
import sys

from setuptools import setup, find_packages


if sys.version_info < (2, 6):
    raise SystemExit("Python 2.6 or later is required.")

exec(open(os.path.join("marrow", "script", "release.py")))



setup(
        name = "marrow.script",
        version = version,
        
        description = "Turn any callable into a powerful command line script through arglist introspection.",
        long_description = """\
The marrow.script package is a small library for turning average every-day
callables (such as functions and class methods) into command-line scripts
while automatically determining argument naming, typecasting, and generating
things like help and version information.  All behavior can be overridden by
you, the developer, giving you a flexible and easy to develop with command
line parsing library to replace ``optparse`` and ``argparse``.  This package
is not a wrapper around existing parsing libraries, and attempts to match the
syntax common to GNU software.

In a larger scope marrow.script aims to replace other high-level command-line
scripting libraries such as Paste Script and commandline while also
implementing Python 3 compatibility.

For full documentation, see the README.textile file present in the package,
or view it online on the GitHub project page:

https://github.com/marrow/marrow.script""",
        
        author = "Alice Bevan-McGregor",
        author_email = "alice+marrow@gothcandy.com",
        url = "https://github.com/marrow/marrow.script",
        license = "MIT",
        
        install_requires = [
            'marrow.util < 2.0'
        ],
        
        test_suite = 'nose.collector',
        tests_require = [
                'nose',
                'coverage'
            ],
        
        classifiers = [
                "Development Status :: 4 - Beta",
                "Environment :: Console",
                "Intended Audience :: Developers",
                "License :: OSI Approved :: MIT License",
                "Operating System :: OS Independent",
                "Programming Language :: Python",
                "Programming Language :: Python :: 2.6",
                "Programming Language :: Python :: 2.7",
                "Programming Language :: Python :: 3",
                "Programming Language :: Python :: 3.1",
                "Programming Language :: Python :: 3.2",
                "Topic :: Software Development :: Libraries :: Python Modules",
                "Topic :: Utilities"
            ],
        
        packages = find_packages(exclude=['examples', 'tests']),
        zip_safe = True,
        include_package_data = True,
        package_data = {'': ['README.textile', 'LICENSE']},
        
        namespace_packages = ['marrow'],
    )

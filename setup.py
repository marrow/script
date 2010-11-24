#!/usr/bin/env python
# encoding: utf-8

import sys, os

try:
    from distribute_setup import use_setuptools
    use_setuptools()

except ImportError:
    pass

from setuptools import setup, find_packages


if sys.version_info <= (2, 6):
    raise SystemExit("Python 2.6 or later is required.")

if sys.version_info >= (3,0):
    def execfile(filename, globals_=None, locals_=None):
        if globals_ is None:
            globals_ = globals()
        
        if locals_ is None:
            locals_ = globals_
        
        exec(compile(open(filename).read(), filename, 'exec'), globals_, locals_)

else:
    from __builtin__ import execfile

execfile(os.path.join("marrow", "script", "release.py"), globals(), locals())



setup(
        name = name,
        version = version,
        
        description = summary,
        long_description = description,
        author = author,
        author_email = email,
        url = url,
        download_url = download_url,
        license = license,
        keywords = '',
        
        install_requires = ['marrow.util'],
        
        test_suite = 'nose.collector',
        tests_require = [
                'nose',
                'coverage'
            ],
        
        classifiers = [
                "Development Status :: 1 - Planning",
                "Environment :: Console",
                "Intended Audience :: Developers",
                "License :: OSI Approved :: MIT License",
                "Operating System :: OS Independent",
                "Programming Language :: Python",
                "Topic :: Internet :: WWW/HTTP :: WSGI",
                "Topic :: Software Development :: Libraries :: Python Modules"
            ],
        
        packages = find_packages(exclude=['examples', 'tests', 'tests.*', 'docs', 'third-party']),
        include_package_data = True,
        package_data = {
                '': ['README.textile', 'LICENSE', 'distribute_setup.py'],
                'docs': ['Makefile', 'source/*']
            },
        zip_safe = True,
        
        namespace_packages = ['marrow'],
        
        entry_points = {}
    )

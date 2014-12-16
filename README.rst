==============
Marrow Package
==============

    © 2014 Alice Bevan-McGregor and contributors.

..

    https://github.com/marrow/package

..

    |latestversion| |downloads| |masterstatus| |mastercover| |issuecount|

1. What is Marrow Package?
==========================

This package is a combination of utilities for handling object lookup, resolving object names, and managing simple to
complex plugin architectures.  Notably it includes a dependency grapher system for extensions and a cross-runtime
method for looking up qualified object names that works on Python 2.6+ and Python 3.2+.

This library is fully unit tested where possible.  (Two untested paths remain relating to use of on-disk directories
for plugin discovery.)


2. Installation
===============

Installing ``marrow.package`` is easy, just execute the following in a terminal::

    pip install marrow.package

**Note:** We *strongly* recommend always using a container, virtualization, or sandboxing environment of some kind when
developing using Python; installing things system-wide is yucky (for a variety of reasons) nine times out of ten.  We prefer light-weight `virtualenv <https://virtualenv.pypa.io/en/latest/virtualenv.html>`_, others prefer solutions as robust as `Vagrant <http://www.vagrantup.com>`_.

If you add ``marrow.package`` to the ``install_requires`` argument of the call to ``setup()`` in your applicaiton's
``setup.py`` file, Marrow Package will be automatically installed and made available when your own application or
library is installed.  We recommend using "less than" version numbers to ensure there are no unintentional
side-effects when updating.  Use ``marrow.package<1.1`` to get all bugfixes for the current release, and
``marrow.package<2.0`` to get bugfixes and feature updates while ensuring that large breaking changes are not installed.


2.1. Development Version
------------------------

    |developstatus| |developcover|

Development takes place on `GitHub <https://github.com/>`_ in the
`marrow.package <https://github.com/marrow/package/>`_ project.  Issue tracking, documentation, and downloads
are provided there.

Installing the current development version requires `Git <http://git-scm.com/>`_, a distributed source code management
system.  If you have Git you can run the following to download and *link* the development version into your Python
runtime::

    git clone https://github.com/marrow/package.git
    (cd package; python setup.py develop)

You can then upgrade to the latest version at any time::

    (cd package; git pull; python setup.py develop)

If you would like to make changes and contribute them back to the project, fork the GitHub project, make your changes,
and submit a pull request.  This process is beyond the scope of this documentation; for more information see
`GitHub's documentation <http://help.github.com/>`_.


3. Getting Object References
============================

Object references describe the module and attribute path needed to resolve the object.  For example, ``foo:bar`` is a
reference that describes importing "foo" prior to retrieving an object named "bar" from the module.  On Python 3.3+ a
useful shortcut is provided, ``__qualname__`` which speeds up this lookup.

For example, let's define a class and get a reference to it::

    from marrow.package.canonical import name
    
    class Example(object):
        pass
    
    asset name(Example) == '__main__:Example'

You can, depending on platform, retrieve a reference to any of the following types of objects:

* Module level:
	* class
	* class instance
	* class method
	* class staticmethod
	* function
	* instance classmethod
	* instance method
	* instance staticmethod
	* shallow nested class
* On Python 3.3+:
	* closure
	* deeply nested class or method


4. Resolving Object References
==============================

Two utilities are provided which allow you resolve string path references to objects.  The first is quite simple::

    from marrow.package.loader import traverse
    
    assert traverse({'foo': {'bar': 27}}, 'foo.bar') == 27

This will search the dictionary described for a "foo" element, then "bar" element.

The ``traverse`` function takes some additional optional arguments.  If ``executable`` is ``True`` any executable
function encountered will be executed without arguments. Traversal will continue on the result of that call.  You can
change the separator as desired, i.e. to a '/' using the ``separator`` argument.

By default attributes (but not array elements) prefixed with an underscore are taboo.  They will not resolve, raising
a LookupError.  You can allow these by setting ``protect`` to ``False``.

Certain allowances are made: if a 'path segment' is numerical, it's treated as an array index. If attribute lookup
fails, it will re-try on that object using array notation and continue from there.  This makes lookup very flexible.


4.1. Resolving Import References
--------------------------------

The more complete API for name resolution uses the ``load`` funciton, which takes the same optional keyword arguments
as ``traverse``.  Additionally, this function accepts an optional ``namespace`` to search for plugins within.  For
example::

    from marrow.package.loader import load
    from pip import main
    
    # Load class Foo from example.objects
    load('example.objects:Foo')
        
    # Load the result of the class method ``new`` of the Foo object
    load('example.objects:Foo.new', executable=True)
    
    # Load the "pip" command-line interface.
    assert load('pip', 'console_scripts') is main

Providing a namespace does not prevent explicit object lookup (dot-colon notation) from working.


4.2. Caching Import References
------------------------------

An attribute-access dictionary is provided that acts as an import cache::

    from marrow.package.cache import PackageCache
    from pip import main
    
    cache = PackageCache('console_scripts')
    
    assert cache.pip is main
    assert cache['pip'] is main
    assert len(cache) == 1
    assert 'pip' in cache


5. Managing Plugins
===================

This package provides two main methods of dealing with plugins and extensions, the first is simple, the second
provides full dependency graphing of the extensions.

5.1. Plugin Manager
-------------------

The ``PluginManager`` class takes two arguments: the first is the entry point ``namespace`` to search, the second is
an optional iterable of folders to add to the Python search path for installed packages, allowing your application to
have a dedicated plugins folder.

It provides a ``register`` method which take a name and the object to use as the plugin and registers it internally,
supporting both attribute and array-like notation for retrieval, as well as iteration of plugins (includes all entry
point plugins found and any custom registered ones).

5.2. Extension Manager
----------------------

At a higher level is a ``PluginManager`` subclass called ``ExtensionManager`` which additoinally exposes a ``sort``
method capable of resolving dependency order for extensions which follow a simple protocol: have an attribute or array
element matching the following, all optional:

* ``provides`` — declare tags describing the features offered by the plugin
* ``needs`` — delcare the tags that must be present for this extension to function
* ``uses`` — declare the tags that must be evaluated prior to this extension, but aren't hard requirements
* ``first`` — declare that this extension is a dependency of all other non-first extensions
* ``last`` — declare that this extension depends on all other non-last extensions


6. Version History
==================

Version 1.0
-----------

* **Initial release.**  Combination of utilities from other Marrow projects.


7. License
==========

Marrow Pacakge has been released under the MIT Open Source license.

7.1. The MIT License
--------------------

Copyright © 2014 Alice Bevan-McGregor and contributors.

Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated
documentation files (the “Software”), to deal in the Software without restriction, including without limitation the
rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit
persons to whom the Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all copies or substantial portions of the
Software.

THE SOFTWARE IS PROVIDED “AS IS”, WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE
WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NON-INFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR
COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR
OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.


.. |masterstatus| image:: http://img.shields.io/travis/marrow/package/master.svg?style=flat
    :target: https://travis-ci.org/marrow/package
    :alt: Release Build Status

.. |developstatus| image:: http://img.shields.io/travis/marrow/package/develop.svg?style=flat
    :target: https://travis-ci.org/marrow/package
    :alt: Development Build Status

.. |latestversion| image:: http://img.shields.io/pypi/v/marrow.package.svg?style=flat
    :target: https://pypi.python.org/pypi/package
    :alt: Latest Version

.. |downloads| image:: http://img.shields.io/pypi/dw/marrow.package.svg?style=flat
    :target: https://pypi.python.org/pypi/package
    :alt: Downloads per Week

.. |mastercover| image:: http://img.shields.io/coveralls/marrow/package/master.svg?style=flat
    :target: https://travis-ci.org/marrow/package
    :alt: Release Test Coverage

.. |developcover| image:: http://img.shields.io/coveralls/marrow/package/develop.svg?style=flat
    :target: https://travis-ci.org/marrow/package
    :alt: Development Test Coverage

.. |issuecount| image:: http://img.shields.io/github/issues/marrow/package.svg?style=flat
    :target: https://github.com/marrow/package/issues
    :alt: Github Issues

.. |cake| image:: http://img.shields.io/badge/cake-lie-1b87fb.svg?style=flat

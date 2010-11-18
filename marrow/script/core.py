# encoding: utf-8

from __future__ import with_statement

import sys
import types
import inspect

from marrow.script.util import getargspec, wrap
from marrow.util.object import NoDefault
from marrow.util.bunch import Bunch
from marrow.util.convert import boolean, array



class Parser(object):
    def __init__(self, obj, help=NoDefault, version=NoDefault):
        self.callable = obj
        
        if help is not NoDefault:
            self.help = help
        
        if version is not NoDefault:
            self.version = version
    
    def __call__(self, argv):
        if inspect.isclass(self.callable):
            return self.execute_class(self.callable, argv)
        
        return self.execute_function(self.callable, argv)
    
    def execute_function(self, fn, argv, top=True):
        spec = self.spec(fn, top)
        args, kwargs, complete = self.process(argv, spec)
        
        if top:
            if kwargs.get('version', False):
                return self.version(fn, spec)
            
            if kwargs.get('help', False) or not complete:
                return self.help(fn, spec)
        
        return fn(*args, **kwargs)
    
    def execute_class(self, cls, argv, top=True):
        pass
    
    def spec(self, fn, top=True):
        arguments, keywords, args, kwargs = getargspec(fn)
        descriptions = getattr(fn, '_cmd_arg_doc', dict())
        types_ = getattr(fn, '_cmd_arg_types', dict())
        args_range = getattr(fn, '_min_args', len(arguments) - len(keywords)), getattr(fn, '_max_args', len(arguments) - len(keywords))
        short = getattr(fn, '_cmd_arg_types', dict())
        
        if top:
            keywords['help'], types_['help'], short['h'], descriptions['help'] = None, boolean, 'help', "Display this help and exit."
            keywords['version'], types_['version'], short['V'], descriptions['version'] = None, boolean, 'version', "Show version and copyright information, then exit."
        
        for name, value in keywords.iteritems():
            if name not in types_:
                if isinstance(value, bool):
                    types_[name] = boolean
                
                elif isinstance(value, (list, tuple)):
                    types_[name] = array
                
                elif value is not None:
                    types_[name] = type(value)
            
            if name not in short.iteritems():
                for i in list(name):
                    if i in short: continue
                    short[i] = name
                    break
        
        return Bunch(
                arguments = arguments,
                keywords = keywords,
                args = args,
                kwargs = kwargs,
                descriptions = descriptions,
                types = types_,
                range = args_range,
                short = short
            )
    
    def process(self, argv, spec):
        """Return usable *args and **kwargs for the given callable spec.
        
        Technically, the *args returned by this method are otherwise unmatched command line arguments.
        """
        
        arguments = list(reversed(spec.arguments))
        args = []
        kwargs = dict(spec.keywords) # default, then override
        seen = {None: True}
        
        state = None # stores "current" argument if using --name value (vs. --name=value)
        nomore = False # If we encounter -- (without a name), stop processing dash-prefixed elements.
        
        # Pre-process the arglist, expanding short-form names into long ones.
        _ = []
        for arg in argv:
            if arg == '--' or '--' in _:
                _.append(arg)
                continue
            
            if arg[0] == '-':
                if arg[1] == '-':
                    _.append(arg)
                    continue
                
                for part in list(arg[1:]):
                    name = spec.short.get(part, None)
                    if name is None or name in seen: raise ValueError
                    
                    _.append('--' + name)
                
                continue
            
            _.append(arg)
        
        argv = _; del _
        
        for arg in argv:
            if arg == '--':
                nomore = True
                continue
            
            if state:
                if not nomore and arg.startswith('-'): raise ValueError
                kwargs[state] = spec.types.get(name, str)(arg)
                state = None
                continue
            
            if not nomore and arg.startswith('--'):
                name, _, value = arg[2:].partition('=')
                if name in seen: raise ValueError
                seen[name] = True
                
                if not value and spec.types.get(name, None) is boolean:
                    kwargs[name] = not kwargs.get(name, False) # if the default is True, save False
                    if name in arguments: arguments.remove(name)
                    continue
                
                if not value:
                    state = name
                    continue
                
                kwargs[name] = spec.types.get(name, str)(value)
                continue
            
            if arguments:
                name = None
                
                while name in seen:
                    # Gracefully handle arguments already explicitly defined by name.
                    # TODO: This -might- be a bad idea; needs testing.  Commented section below is the other option.
                    name = arguments.pop()
                
                # if name in seen: raise ValueError
                
                seen[name] = True
                kwargs[name] = spec.types.get(name, str)(arg)
                continue
            
            remaining.append(arg)
        
        complete = len([i for i in kwargs if i in spec.arguments]) == len(spec.arguments)
        
        return args, kwargs, complete
    
    def help(self, obj, spec):
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
        
        doc, doc2 = partitionhelp(getattr(obj, '__doc__', None))
        if doc: print wrap(doc)
        
        print 'Usage:', sys.argv[0],
        if spec.keywords: print '[OPTIONS]',
        
        for arg in spec.arguments:
            if arg in spec.keywords: continue
            print '<%s>' % arg,
        
        keywords = dict(spec.keywords)
        types = dict(spec.types)
        docs = dict(spec.descriptions)
        
        if keywords:
            print "\n\nOPTIONS may be one or more of:\n"
            help = dict()
            
            for name, default in keywords.iteritems():
                if types.get(name, None) is boolean:
                    help["--" + name] = docs.get(name, "Toggle this value.\nDefault: %r" % default)
                    continue
                
                if types.get(name, True) is None:
                    help["--" + name] = docs.get(name, "Magic option.")
                    continue
                
                help["--" + name + "=VAL"] = docs.get(name, "Override this value.\nDefault: %r" % default)
            
            mlen = max([len(i) for i in help])
            
            for name in sorted(help):
                print " %-*s  %s" % (mlen, name, wrap(help[name]).replace("\n", "\n" + " " * (mlen + 3)))
        
        if doc2: print "\n", wrap(doc2)
    
    def version(self, obj, spec):
        print sys.argv[0],
        
        try:
            print "(" + obj.__title__ + ")",
        
        except AttributeError:
            pass
        
        print obj.__version__
        
        try:
            print "\n" + wrap(obj.__copyright__)
        
        except AttributeError:
            pass

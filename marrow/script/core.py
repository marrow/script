# encoding: utf-8

from __future__ import print_function
from __future__ import unicode_literals

import os
import sys
import types
import inspect

from marrow.util.compat import binary, unicode
from marrow.util.object import NoDefault
from marrow.util.bunch import Bunch
from marrow.util.convert import boolean, array
from marrow.script.util import getargspec, wrap, partitionhelp



class Parser(object):
    def __init__(self, obj, help=NoDefault, version=NoDefault):
        self.callable = obj
        
        if help is not NoDefault:
            self.help = help
        
        if version is not NoDefault:
            self.version = version
    
    def __call__(self, argv=None):
        if argv is None: argv = []
        argv = [(i.decode(sys.getdefaultencoding()) if isinstance(i, binary) else i) for i in argv]
        
        if inspect.isclass(self.callable):
            return self.execute_class(self.callable, argv)
        
        return self.execute_function(self.callable, argv)
    
    def execute_function(self, fn, argv, top=True):
        spec = self.spec(fn, top)
        args, kwargs, complete = self.process(fn, argv, spec)
        
        if top:
            if kwargs.get('version', False):
                return self.version(fn, spec)
            
            if kwargs.get('help', False) or not complete:
                return self.help(fn, spec)
        
        try:
            del kwargs['help'], kwargs['version']
        except:
            pass
        
        return fn(*args, **kwargs)
    
    def execute_class(self, cls, argv, top=True):
        spec = self.spec(cls, top)
        
        args, kwargs, complete = self.process(cls, argv, spec)
        
        if kwargs.get('version', False):
            return self.version(fn, spec)
        
        if kwargs.get('help', False) or not complete or not args or not args[0][0].isalpha():
            return self.help(cls, spec)
        
        try:
            del kwargs['help'], kwargs['version']
        except:
            pass
        
        instance = cls(**kwargs)
        cmdname = args.pop(0)
        cmd = getattr(instance, cmdname, None)
        
        if cmd is None:
            print("Unknown command:", cmdname)
            return self.help(cls, spec)
        
        spec = self.spec(cmd, False)
        
        args, kwargs, complete = self.process(cmd, args, spec)
        
        if kwargs.get('help', False) or not complete:
            return self.help((cls, cmd), spec)
        
        try:
            del kwargs['help']
        except:
            pass
        
        return cmd(*args, **kwargs)
    
    def spec(self, fn, top=True):
        arguments, keywords, args, kwargs = getargspec(fn)
        descriptions = getattr(fn, '_cmd_arg_doc', dict())
        types_ = getattr(fn, '_cmd_arg_types', dict())
        args_range = getattr(fn, '_min_args', len(arguments) - len(keywords)), getattr(fn, '_max_args', len(arguments) - len(keywords))
        short = getattr(fn, '_cmd_shorts', dict())
        
        keywords['help'], types_['help'], short['h'], descriptions['help'] = None, boolean, 'help', "Display this help and exit."
        
        if top:
            keywords['version'], types_['version'], short['V'], descriptions['version'] = None, boolean, 'version', "Show version and copyright information, then exit."
        
        arguments = [i for i in arguments if i not in keywords]
        
        for name in keywords:
            value = keywords[name]
            if name not in types_:
                if isinstance(value, bool):
                    types_[name] = boolean
                
                elif isinstance(value, (list, tuple)):
                    types_[name] = array
                
                elif value is not None:
                    types_[name] = type(value)
            
            if name not in short.values():
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
    
    def process(self, obj, argv, spec):
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
                
                for part in list(arg[1:]): # TODO: Give positional arguments short names.
                    name = spec.short.get(part, None)
                    if name in seen: raise ValueError
                    
                    _.append('--' + name)
                
                continue
            
            _.append(arg)
        
        argv = _; del _
        
        unhandled = False
        
        for arg in argv:
            if arg == '--':
                nomore = True
                continue
            
            if state:
                if not nomore and arg.startswith('-'): raise ValueError
                kwargs[state] = spec.types.get(state, str)(arg)
                state = None
                continue
            
            if not nomore and arg.startswith('--'):
                name, _, value = arg[2:].partition('=')
                
                if (inspect.isclass(obj) and unhandled) or name in seen or name not in kwargs:
                    args.append(arg)
                    continue
                
                seen[name] = True
                
                if not value and spec.types.get(name, None) is boolean:
                    kwargs[name] = not kwargs.get(name, False) # if the default is True, save False
                    if name in arguments: arguments.remove(name)
                    continue
                
                if not value:
                    state = name
                    continue
                
                try:
                    kwargs[name] = spec.types.get(name, str)(value)
                
                except:
                    return [], {}, False
                
                continue
            
            if arguments:
                name = arguments.pop()
                
                if name in seen or name in kwargs:
                    unhandled = True
                    args.append(arg)
                    continue
                
                seen[name] = True
                
                try:
                    kwargs[name] = spec.types.get(name, str)(arg)
                
                except:
                    return [], {}, False
                
                continue
            
            args.append(arg)
        
        complete = len([i for i in kwargs if i in spec.arguments]) == len(spec.arguments)
        
        return args, kwargs, complete
    
    def help(self, obj, spec):
        cls = None
        
        if isinstance(obj, tuple):
            cls, obj = obj
        
        doc, doc2 = partitionhelp(getattr(obj, '__doc__', None))
        
        if doc:
            print(wrap(doc))
        
        print('Usage:', os.path.basename(sys.argv[0]), end=' ')
        
        if not cls and spec.keywords:
            print('[OPTIONS] ', end='')
        
        elif cls:
            print('[OPTIONS] ...', obj.__name__, end=' ')
            if spec.keywords:
                print('[CMDOPTS] ', end='')
        
        if spec.kwargs: print('[--name=value...] ', end='')
        
        for arg in spec.arguments:
            if arg in spec.keywords: continue
            print('<%s> ' % arg, end='')
        
        if spec.args:
            print('[value...] ', end='')
        
        if inspect.isclass(obj):
            print('<COMMAND> [CMDOPTS] ...', end='')
        
        keywords = dict(spec.keywords)
        types = dict(spec.types)
        docs = dict(spec.descriptions)
        shorts = dict([(spec.short[i], i) for i in spec.short])
        
        if keywords:
            print("\n\n", "CMDOPTS" if cls else "OPTIONS" , " may be one or more of:\n", sep='')
            help = dict()
            
            for name in keywords:
                default = keywords[name]
                if types.get(name, None) is boolean:
                    help["-" + shorts[name] + ", --" + name] = docs.get(name, "Toggle this value.\nDefault: %r" % default)
                    continue
                
                if types.get(name, True) is None:
                    help["-" + shorts[name] + ", --" + name] = docs.get(name, "Magic option.")
                    continue
                
                help["-" + shorts[name] + ", --" + name + "=VAL"] = docs.get(name, "Override this value.\nDefault: %r" % default)
            
            mlen = max([len(i) for i in help])
            
            for name in sorted(help):
                print(" %-*s  %s" % (mlen, name, wrap(help[name]).replace("\n", "\n" + " " * (mlen + 3))))
        
        if inspect.isclass(obj):
            print('\nCOMMAND may be one of:\n')
            
            cmds = dict()
            for cmd in dir(obj):
                if cmd[0] == '_': continue
                
                h1, h2 = partitionhelp(getattr(getattr(obj, cmd), '__doc__', "No information available."))
                
                cmds[cmd] = h1
            
            mlen = max([len(i) for i in cmds])
            
            for name in sorted(cmds):
                print(" %-*s  %s" % (mlen, name, wrap(cmds[name]).replace("\n", "\n" + " " * (mlen + 3))))
            
            print(wrap("\nFor help on a specific command, call the command and pass --help in CMDOPTS."))
        
        if doc2: print("\n", wrap(doc2), sep='')
        
        print()
        
        return os.EX_USAGE
    
    def version(self, obj, spec):
        print(sys.argv[0], end='')
        
        try:
            print("(" + obj._cmd_script['title'] + ")", end='')
        
        except AttributeError:
            pass
        
        except KeyError:
            pass
        
        try:
            print(obj._cmd_script['version'])
        
        except AttributeError:
            pass
        
        except KeyError:
            pass
        
        try:
            print("\n" + wrap(obj._cmd_script['copyright']))
        
        except AttributeError:
            pass
        
        except KeyError:
            pass
        
        return os.EX_USAGE
    

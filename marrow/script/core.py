# encoding: utf-8

from __future__ import print_function
from __future__ import unicode_literals

import os
import sys
import inspect

from pprint import pformat

from marrow.util.compat import binary, unicode, exception
from marrow.util.object import NoDefault
from marrow.util.bunch import Bunch
from marrow.util.convert import boolean, array
from marrow.script.util import getargspec, wrap, partitionhelp


__all__ = ['ExitException', 'Parser']


# Mac OS X terminal lies, so do others, probably.
# TODO: Needs testing; works on OS X.
encoding = sys.getdefaultencoding() if sys.getdefaultencoding() != 'ascii' else 'utf8'



class ExitException(Exception):
    pass


class Parser(object):
    def __init__(self, obj, help=NoDefault, version=NoDefault):
        self.callable = obj
        
        if help is not NoDefault:
            self.help = help
        
        if version is not NoDefault:
            self.version = version
    
    def __call__(self, argv=None):
        try:
            #print(repr(self.callable))
            
            spec = self.spec(self.callable)
            #print(pformat(dict(spec)))
            
            argv = self.prepare(argv, spec)
            #print(pformat(argv))
            
            details = self.process(argv, spec)
            #print(pformat(dict(details)))
            
            if not spec.cls and ( not details.complete or ( not spec.args and details.remainder ) ):
                print("Incomplete argument list.")
                self.help(True, spec)
            
            if not spec.cls:
                return self.callable(*details.args, **details.kwargs) or 0
            
            if not details.complete:
                print("Incomplete argument list.")
                self.help(True, spec)
            
            instance = self.callable(*details.args, **details.kwargs)
            
            if not [i for i in details.remainder if i[0] != '-']:
                self.help(True, spec)
            
            command = [i for i in details.remainder if i[0] != '-'][0]
            details.remainder.remove(command)
            
            try:
                command = getattr(instance, command)
            
            except AttributeError:
                print("Unknown command:", command)
                self.help(True, spec)
            
            cmd_spec = self.spec(command, instance)
            cmd_spec.cls = self.callable
            #print(pformat(dict(cmd_spec)))
            
            argv = self.prepare(details.remainder, cmd_spec)
            
            cmd_details = self.process(argv, cmd_spec)
            #print(pformat(dict(cmd_details)))
            
            if not cmd_details.complete:
                print("Incomplete argument list.")
                self.help(True, spec)
            
            if cmd_details.remainder:
                print("Unexpected arguments.")
                self.help(True, spec)
            
            return command(*cmd_details.args, **cmd_details.kwargs) or 0
        
        except ExitException:
            exc = exception().exception
            
            if exc.args[1]:
                print(exc.args[1])
            
            return exc.args[0]
    
    def prepare(self, argv, spec):
        # Handle empty argument list.
        if argv is None: argv = []
        
        # Expand single-hyphen arguments to their long form.
        argv_ = []
        for arg in argv:
            # Convert to unicode.
            arg = arg.decode(encoding) if isinstance(arg, binary) else arg
            
            # Skip empty arguments.  Don't know how we can have these, though...
            if not arg: continue
            
            # A double-hyphen argument signals the end of hyphenated arguments.
            if arg == '--' or '--' in argv_:
                argv_.append(arg)
                continue
            
            if arg[0] == '-':
                if arg[1] == '-':
                    argv_.append(arg)
                    continue
                
                for part in list(arg[1:]):
                    name = spec.short.get(part, None)
                    if name is None: raise Exception('Unknown argument "-' + part + '".')
                    argv_.append('--' + name)
                
                continue
            
            argv_.append(arg)
        
        return argv_
    
    def spec(self, obj, top=True):
        is_class = inspect.isclass(obj)
        
        # Load up the canonical argument specification.
        arguments, keywords, args, kwargs = getargspec(obj)
        
        # Load up decorator-provided details.
        docs = getattr(obj, '_cmd_arg_doc', dict())
        conv = getattr(obj, '_cmd_arg_types', dict())
        short = getattr(obj, '_cmd_shorts', dict())
        callbacks = getattr(obj, '_cmd_callbacks', dict())
        
        # Pre-process some of the data.
        for name in sorted(keywords.keys()):
            # Remove keyword arguments from argument list.
            if name in arguments:
                arguments.remove(name)
            
            # Determine if we need to typecast data automatically.
            if name not in conv:
                value = keywords[name]
                if isinstance(value, bool): conv[name] = boolean
                elif isinstance(value, (list, tuple)): conv[name] = array
                elif value is not None: conv[name] = type(value)
            
            if name not in short.values():
                for i in list(name):
                    if i in short: continue
                    short[i] = name
                    break
        
        minmax = getattr(obj, '_min_args', len(arguments)), getattr(obj, '_max_args', None if args else len(arguments))
        
        # -h/--help is always an option.
        keywords['help'], conv['help'], short['h'], docs['help'], callbacks['help'] = \
                False, boolean, 'help', "Display this help and exit.", self.help
        
        # -V/--version is an option if we are inspecting a class or not using classes at all.
        if top and hasattr(obj, '_cmd_script'):
            keywords['version'], conv['version'], short['V'], docs['version'], callbacks['version'] = \
                    False, boolean, b'version', "Show version and copyright information, then exit.", self.version
        
        return Bunch(
                cls = is_class,
                obj = obj,
                arguments = arguments,
                keywords = keywords,
                args = args,
                kwargs = kwargs,
                docs = docs,
                conv = conv,
                range = minmax,
                short = short,
                callbacks = callbacks
            )
    
    def process(self, argv, spec):
        args = [] # positional arguments to the callable defined by spec
        kwargs = {} # keyword arguments to the callable defined by spec
        remainder = [] # values otherwise unmatched
        state = None # kwarg name the next argument will fill
        
        for argument in argv:
            if state:
                if state not in spec.keywords:
                    remainder.extend(['--' + state.decode('ascii'), argument])
                    continue
                
                try:
                    kwargs[state] = spec.callbacks.get(state, lambda a, b: a)(spec.conv.get(state, unicode)(argument), spec)
                except:
                    self.help(True, spec)
                
                state = None
                continue
            
            if argument == '--':
                state = False
                continue
            
            if state is not False and argument[0] == '-':
                #print("longarg:", argument)
                argument = argument[2:]
                
                if '=' not in argument:
                    argument = argument.encode('ascii')
                    
                    if spec.conv.get(argument, None) is boolean:
                        # if the default is True, save False
                        try:
                            #print("bool:", repr(spec.callbacks.get(argument, lambda a, b: a)), repr(spec.keywords.get(argument, False)))
                            kwargs[argument] = spec.callbacks.get(argument, lambda a, b: a)(not spec.keywords.get(argument, False), spec)
                        
                        except ExitException:
                            raise
                        
                        except:
                            self.help(True, spec)
                        
                        continue
                    
                    state = argument
                    continue
                
                argument, _, value = argument.partition('=')
                argument = argument.encode('ascii')
                
                if not spec.kwargs and argument not in spec.keywords:
                    remainder.append('--' + argument.decode('ascii') + '=' + value)
                    continue
                
                try:
                    kwargs[argument] = spec.callbacks.get(argument, lambda a, b: a)(spec.conv.get(argument, unicode)(value), spec)
                
                except ExitException:
                    raise
                
                except:
                    self.help(True, spec)
                
                continue
            
            if spec.range[1] is None or len(args) < spec.range[1]:
                if len(args) >= len(spec.arguments):
                    args.append(argument)
                    continue
                
                name = spec.arguments[len(args)]
                args.append(spec.callbacks.get(name, lambda a, b: a)(spec.conv.get(name, unicode)(argument), spec))
                continue
            
            if spec.cls is True:
                state = False
            
            remainder.append(argument)
        
        complete = spec.range[0] <= len(args) <= (spec.range[1] if spec.range[1] is not None else 65534)
        
        if 'help' in kwargs: del kwargs['help']
        if 'version' in kwargs: del kwargs['version']
        
        return Bunch(complete=complete, args=args, kwargs=kwargs, remainder=remainder)
    
    def help(self, arg, spec):
        obj = spec.obj
        cls = spec.cls
        
        doc, doc2 = partitionhelp(getattr(obj, '__doc__', None))
        
        if doc: print(wrap(doc))
        
        print('Usage:', os.path.basename(sys.argv[0]), end=' ')
        
        if spec.keywords and cls is True or cls is None:
            print('[OPTIONS] ', end='')
        
        elif cls is not None and cls is not True:
            print('[OPTIONS] ...', obj.__name__, end=' ')
            if spec.keywords:
                print('[CMDOPTS] ', end='')
        
        if spec.kwargs: print('[--name=value...] ', end='')
        
        for arg in spec.arguments:
            if arg in spec.keywords: continue
            print('<%s> ' % arg, end='')
        
        if spec.args:
            print('[value...] ', end='')
        
        if cls is True:
            print('<COMMAND> ...', end='')
        
        keywords = dict(spec.keywords)
        conv = dict(spec.conv)
        docs = dict(spec.docs)
        shorts = dict([(spec.short[i], i) for i in spec.short])
        
        if keywords:
            print("\n\n", "CMDOPTS" if cls is not None and cls is not True else "OPTIONS" , " may be one or more of:\n", sep='')
            help = dict()
            
            for name in keywords:
                default = keywords[name]
                
                if conv.get(name, None) is boolean:
                    help["-" + shorts[name] + ", --" + name] = docs.get(name, "Toggle this value.\nDefault: %r" % default)
                    continue
                
                if conv.get(name, True) is None:
                    help["-" + shorts[name] + ", --" + name] = docs.get(name, "Magic option.")
                    continue
                
                help["-" + shorts[name] + ", --" + name + "=VAL"] = docs.get(name, "Override this value.\nDefault: %r" % default)
            
            mlen = max([len(i) for i in help])
            
            for name in sorted(help):
                print(" %-*s  %s" % (mlen, name, wrap(help[name]).replace("\n", "\n" + " " * (mlen + 3))))
        
        if spec.cls is True:
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
        raise ExitException(os.EX_USAGE, None)
    
    def version(self, arg, spec):
        print(os.path.basename(sys.argv[0]), end='')
        
        try:
            print("(" + spec.obj._cmd_script['title'] + ")", end='')
        
        except AttributeError:
            pass
        
        except KeyError:
            pass
        
        if 'version' in spec.obj._cmd_script:
            print(spec.obj._cmd_script['version'])
        
        try:
            print("\n" + wrap(spec.obj._cmd_script['copyright']))
        
        except (AttributeError, KeyError):
            print()
        
        print()
        raise ExitException(os.EX_USAGE, None)

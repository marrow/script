# encoding: utf-8

from __future__ import print_function
from __future__ import unicode_literals

import os
import sys
import inspect

from pprint import pformat
from functools import partial

from marrow.util.bunch import Bunch
from marrow.util.compat import binary, unicode
from marrow.util.convert import boolean, array
from marrow.script.util import getargspec, wrap, partitionhelp


__all__ = ['ExitException', 'ScriptError', 'MalformedArguments', 'Parser']


# Mac OS X terminal lies, so do others, probably.
# TODO: Needs testing; works on OS X.
encoding = sys.getdefaultencoding() if sys.getdefaultencoding() != 'ascii' else 'utf8'

log = __import__('logging').getLogger(__name__)


class ExitException(Exception):
    pass


class ScriptError(Exception):
    pass


class MalformedArguments(ScriptError):
    pass


class Parser(object):
    def __init__(self, obj):
        self.callable = obj
    
    def __call__(self, argv=None, *args):
        # Gather together the argument list.
        arguments = ([argv] + list(args)) if args else ((argv if isinstance(argv, list) else [argv]) if argv else [])
        
        # Determine initial argument specification.
        master = self.specification
        
        consumed = []
        
        i = 0
        
        try:
            while i < len(master.callables):
                spec = master.callables[i]
                
                args, kwargs, arguments = self.process(spec, arguments)
                
                print(args, spec.arguments)
                if len(args) < len(spec.arguments):
                    raise ExitException(os.EX_USAGE, "Additional positional arguments required.")
                
                if spec.simple:
                    # Final callable.
                    
                    if arguments:
                        # Argument overflow; too many argumnets.
                        raise ExitException(os.EX_USAGE, "Too many arguments: %r" % arguments)
                    
                    # We've reached the end.
                    consumed.append(Bunch(spec=spec, obj=spec.obj, args=args, kwargs=kwargs))
                    break
                
                if not arguments:
                    # Argument underflow; need sub-command, not specified.
                    raise ExitException(os.EX_USAGE, "Must specify command to execute.")
                
                # Handle sub-commands.
                # TODO: Handle class instance with __call__.
                
                obj = spec.obj(*args, **kwargs)
                
                consumed.append(Bunch(spec=spec, obj=obj, args=args, kwargs=kwargs))
                
                name = arguments.pop(0)
                sub = getattr(obj, name)
                
                if name[0] == '_' or not sub or not hasattr(sub, '__call__'):
                    raise ExitException(os.EX_USAGE, "Invalid command.")
                
                master.callables.append(self.specification_for(sub, master))
                
                i += 1
            
            executable = consumed[-1]
            return executable.obj(*executable.args, **executable.kwargs) or 0
        
        except ExitException, e:
            code, message = e.args
            
            if message:
                print(message)
            
            if code == os.EX_USAGE and message is not None:
                help = master.callables[-1].callback.get('help')
                
                if not help:
                    print("Help not available.")
                    return code
                
                try:
                    help(True)
                
                except ExitException, e:
                    code, message = e.args
            
            return code
    
    @property
    def specification(self):
        """Determine the high-level script specification.
        
        Additionally, prepare the way for sub-command calling.
        """
        
        spec = Bunch(
                name = None,
                author = None,
                version = None,
                copyright = None,
                license = None,
                url = None
            )
        
        # TODO: Load some of this from setuptools.
        spec.update(getattr(self.callable, '_cmd_script_info', dict()))
        
        spec.callables = [
                self.specification_for(self.callable, spec)
            ]
        
        return spec
    
    def specification_for(self, obj, master):
        # Load up the canonical argument specification.
        arguments, keywords, args, kwargs = getargspec(obj)
        docstring, typecast, abbreviation, callback = dict(), dict(), dict(), dict()
        
        # Pre-process the argument lists.
        for name, value in sorted(zip(keywords.keys(), keywords.values())):
            # Remove keyword arguments from positional list.
            if name in arguments:
                arguments.remove(name)
            
            # Determine typecasting information.
            if isinstance(value, bool): typecast[name] = boolean
            elif isinstance(value, (list, tuple)): typecast[name] = array
            elif value is not None: typecast[name] = type(value)
            
            # Determine abbreviations.
            for char in name:
                if char in abbreviation: continue
                abbreviation[char] = name
                break
            
            else:
                if name not in getattr(obj, '_cmd_arg_abbrev', dict()):
                    raise MalformedArguments("Unable to determine unique abbreviation for %s argument to %r." \
                                             " Specify one using the @abbreviation decorator." % (name, obj))
        
        # Flip it around for more logical (and consistent) user assignment.
        abbreviation = dict(zip(abbreviation.values(), abbreviation.keys()))
        
        # Load up decorator-provided details.
        decorated = obj.__init__ if inspect.isclass(obj) else obj
        docstring.update(getattr(decorated, '_cmd_arg_doc', dict()))
        typecast.update(getattr(decorated, '_cmd_arg_type', dict()))
        abbreviation.update(getattr(decorated, '_cmd_arg_abbrev', dict()))
        callback.update(getattr(decorated, '_cmd_arg_callback', dict()))
        minmax = (getattr(decorated, '_min_args', len(arguments)),
            getattr(decorated, '_max_args', 65534 if args else len(arguments)))
        
        # -h/--help is always an option.
        keywords.setdefault(b'help', False)
        typecast.setdefault(b'help', boolean)
        abbreviation.setdefault(b'help', b'h')
        docstring.setdefault(b'help', b"Display this help and exit.")
        callback.setdefault(b'help', partial(self.help, master))
        
        # Flip it back for easier processing later.
        abbreviation = dict(zip(abbreviation.values(), abbreviation.keys()))
        
        return Bunch(
                obj = obj,
                
                doc = getattr(obj, '__doc__', None) or None,
                simple = not inspect.isclass(obj),
                direct = hasattr(obj, '__call__') and not inspect.isclass(obj),
                
                arguments = arguments,
                keywords = keywords,
                args = args,
                kwargs = kwargs,
                
                docstring = docstring,
                typecast = typecast,
                abbreviation = abbreviation,
                callback = callback,
                
                range = minmax
            )
    
    def prepare(self, spec, arguments):
        """Expand short arguments into long ones and expand equations.
        
        This only handles arguments we know of and may be called multiple
        times to handle subcommands.
        """
        
        newarguments = list()
        
        for arg in arguments:
            # Ensure arguments are unicode.  We handle Python 2 str keywords later.
            arg = arg.decode(encoding) if isinstance(arg, binary) else arg
            
            # Skip (impossible?) empty arguments.
            if not arg: continue
            
            # A double-hyphen argument signals the end of hyphenated arguments.
            if arg == '--' or '--' in newarguments:
                newarguments.append(arg)
                continue
            
            if arg[0] == '-':
                if arg[1] == '-':
                    n, _, v = arg.partition('=')
                    
                    newarguments.append(n)
                    
                    # Unpack the argument's value, if one exists.
                    if v: newarguments.append(v)
                    
                    continue
                
                # Expand short arguments into long ones.
                for part in list(arg[1:]):
                    name = spec.abbreviation.get(part, None)
                    
                    # Some arguments might not be able to be processed right now;
                    # we file this away for potential use by sub-commands.
                    if not name: newarguments.append('-' + part)
                    else: newarguments.append('--' + name)
                
                continue
            
            # Positional arguments just passed through.
            newarguments.append(arg)
        
        return newarguments
    
    def process(self, spec, arguments):
        arguments = self.prepare(spec, arguments)
        arguments.reverse()
        
        remainder = []
        args = []
        kwargs = {}
        
        parsing = True
        
        def value_for(name, value):
            # TODO: Fallback on help if the following fails.
            
            if name is None:
                return value
            
            try:
                cast = spec.typecast.get(name)
                value = cast(value) if cast else value
                
                callback = spec.callback.get(name)
                arg = callback(value) if callback else value
            
            except ExitException:
                raise
            
            except:
                
                log.exception("Error processing typecasting or callback for %s argument." % (name))
                raise ExitException(os.EX_USAGE, None)
            
            return value
        
        while arguments:
            arg = arguments.pop()
            
            if arg == '--':
                # Stop processing keyword arguments.
                parsing = False
                continue
            
            if not parsing or ( arg[:2] != '--' and len(args) < spec.range[1] ):
                # Positional argument.
                args.append(value_for(spec.arguments[len(args)] if len(args) < len(spec.arguments) else None, arg))
                continue
            
            if (arg[0] == '-' and arg[1] != '-') or \
                    (arg[:2] == '--' and arg[2:] not in spec.keywords and not spec.kwargs) or \
                    (arg[:2] != '--' and len(args) == spec.range[1]):
                
                # Unknown (keyword) argument or too many positional values, exiting early.
                remainder.append(arg)
                remainder.extend(reversed(arguments))
                break
            
            # Keyword argument.
            
            arg = arg[2:].encode('ascii', 'ignore')
            
            if spec.typecast.get(arg, None) is boolean:
                kwargs[arg] = value_for(arg, not spec.keywords.get(arg, False))
                continue
            
            kwargs[arg] = value_for(arg, arguments.pop())
        
        return args, kwargs, remainder
    
    def help(self, master, value):
        width = 79
        
        # Determine current terminal width, if possible.
        if sys.stdout.isatty():
            try:
                # Use terminal control codes if possible.
                import fcntl, termios, struct
                width = struct.unpack(b'hh', fcntl.ioctl(sys.stdout.fileno(), termios.TIOCGWINSZ, '1234'))[1] - 1
            
            except:
                # Fall back on environment variables.
                try:
                    width = int(os.environ['COLUMNS']) - 1
                except:
                    # TODO: Fall back on curses, then ANSI.
                    pass
        
        # Output the summary information.
        for current, spec in enumerate(master.callables):
            summary, description = partitionhelp(spec.doc)
            
            if current == 0 and summary: print(wrap(summary, width))
            
            if current == 0:
                print("Usage:", os.path.basename(sys.argv[0]), end=" ")
            
            else:
                print(spec.obj.__name__, end=" ")
            
            if spec.keywords:
                print("[OPTIONS]" if current == 0 else "[CMDOPTS]", end=" ")
            
            if spec.kwargs:
                print("[--name=value...]", end=" ")
            
            for arg in spec.arguments:
                print("<", arg, ">", sep="", end=" ")
            
            if spec.args:
                print("[value...]", end=" ")
            
            if not spec.simple and len(master.callables) == current + 1:
                print("<COMMAND> ...", end="")
        
        print()
        
        # Output the details.
        for current, spec in enumerate(master.callables):
            summary, description = partitionhelp(spec.doc)
            
            if current != 0:
                print("\nCommand:", spec.obj.__name__)
                if summary: print(wrap(summary, width))
            
            if spec.keywords:
                print("\n", "OPTIONS" if current == 0 else "CMDOPTS", " may be one or more of:", sep="", end="\n\n")
                
                strings = dict()
                abbreviation = dict(zip(spec.abbreviation.values(), spec.abbreviation.keys()))
                
                for name in spec.keywords:
                    default = spec.keywords[name]
                    
                    if spec.typecast.get(name, None) is boolean:
                        strings["-" + abbreviation[name] + ", --" + name] = \
                                spec.docstring.get(name, "Toggle this value.\nDefault: %r" % default)
                        continue
                    
                    strings["-" + abbreviation[name] + ", --" + name + "=VAL"] = \
                            spec.docstring.get(name, "Override this value.\nDefault: %r" % default)
                
                mlen = max([len(i) for i in strings])
                for name in sorted(strings):
                    print(" %-*s  %s" % (mlen, name, wrap(strings[name], width).replace("\n", "\n" + " " * (mlen + 3))))
            
            if not spec.simple and len(master.callables) == current + 1:
                print("\n", "COMMAND may be one of:", sep="", end="\n\n")
                
                cmds = dict()
                for cmd in dir(spec.obj):
                    if cmd[0] == '_' or not callable(getattr(spec.obj, cmd)): continue
                    cmds[cmd] = partitionhelp(getattr(spec.obj, cmd).__doc__ or "Undocumented command.")[0]
                
                mlen = max([len(i) for i in cmds])
                for name in sorted(cmds):
                    print(" %-*s  %s" % (mlen, name, wrap(cmds[name], width).replace("\n", "\n" + " " * (mlen + 3))))
                
                print("\n", wrap("For help on a specific command, call the command and pass --help in CMDOPTS.", width), sep="")
            
            if description: print("\n", wrap(description, width), sep="")
        
        print()
        raise ExitException(os.EX_USAGE, None)

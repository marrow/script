# encoding: utf-8

from __future__ import print_function
from __future__ import unicode_literals

import os
import sys

from inspect import getargspec, getdoc, isfunction, ismethod, isclass

from marrow.util.bunch import Bunch
from marrow.util.convert import boolean, array
from marrow.script.util import wrap, partitionhelp


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
    def __init__(self, command):
        self.command = command
        self.stack = []

    def __call__(self, argv=None, *args):
        # Gather together the argument list.
        arguments = ([argv] + list(args)) if args else ((argv if isinstance(argv, list) else [argv]) if argv else [])

        def help():
            try:
                self.stack[-1].callbacks['help'](True, self.stack[-1])
            except ExitException:
                pass

            return os.EX_USAGE

        try:
            return self.execute(arguments) or 0

        except ExitException as e:
            return e.args[0]

        except MalformedArguments as e:
            if not self.stack: raise
            print("Malformed arguments:", e.args[0])
            return help()

        except Exception as e:
            if not self.stack: raise
            log.exception("Uncaught exception.")
            return help()

    def execute(self, arguments):
        parent = None
        current = self.command
        self.stack = []

        while True:
            spec = self.specification(of=current, via=parent)
            self.stack.append(spec)

            arguments = self.expand(arguments, via=spec)
            args, kwargs, arguments = self.arguments(arguments, via=spec)

            if (arguments and not spec.cls) or \
                    (spec.cls and arguments and arguments[0][0] == '-'):
                raise MalformedArguments("Unknown argument: " + arguments[0])

            if len(args) < spec.range[0]:
                raise MalformedArguments("Insufficient positional arguments.")

            if not spec.cls:
                return spec.callable(*args, **kwargs)

            parent = spec.instance = spec.target(*args, **kwargs)

            if not arguments:
                raise MalformedArguments("Command not specified.")

            current = getattr(spec.instance, arguments.pop(0))

    def specification(self, of, defaults=True, via=None):
        """Build our internal specification of the target callable.

        Optionally, pre-populate the callbacks for --help/-h and --version/-V.
        """

        cmd = Bunch(target=of)
        cmd.doc = partitionhelp(getdoc(cmd.target)) if getdoc(cmd.target) else None
        cmd.cls = isclass(cmd.target)
        cmd.fn = isfunction(cmd.target)
        cmd.method = ismethod(cmd.target)
        cmd.callable = cmd.target.__init__ if cmd.cls else cmd.target
        
        try:
            cmd.spec = getargspec(cmd.callable)
        except TypeError:
            # __init__ of built-in class, such as object
            cmd.spec = Bunch(args=['self'], varargs=None, keywords=None, defaults=None)
        
        cmd.trans = dict((i.replace('_', '-'), i) for i in cmd.spec.args)
        cmd.positional = cmd.spec.args[:len(cmd.spec.args)-len(cmd.spec.defaults or [])]
        cmd.named = cmd.spec.args[len(cmd.spec.args)-len(cmd.spec.defaults or []):]
        cmd.defaults = dict((i, j) for i, j in zip(reversed(cmd.spec.args), reversed(cmd.spec.defaults or [])))
        cmd.instance = None
        cmd.indexed = cmd.spec.varargs
        cmd.keyed = cmd.spec.keywords
        cmd.docs = dict()
        cmd.parent = via

        if cmd.cls or cmd.method:
            cmd.positional = cmd.positional[1:]

        cmd.range = (len(cmd.positional), 65535 if cmd.spec.varargs else len(cmd.positional))

        cast = dict()
        short = dict()
        callbacks = dict()

        if defaults:
            cmd.named.extend(('help', 'version'))
            callbacks.update(help=self.help, version=self.version)
            short.update(h='help', V='version')
            cast.update(help=boolean, version=boolean)

        for name in sorted(cmd.defaults):
            # Determine typecasting information.
            if isinstance(cmd.defaults[name], bool): cast[name] = boolean
            elif isinstance(cmd.defaults[name], (list, tuple)): cast[name] = array
            elif cmd.defaults[name] is not None: cast[name] = type(cmd.defaults[name])

            # Determine abbreviations.
            for char in "".join(i for j in zip(name, name.upper()) for i in j):
                if char in short: continue
                short[char] = name
                break

        cmd.cast = cast
        cmd.short = short
        cmd.callbacks = callbacks

        return cmd

    def help(self, value, via):
        """Display a GNU-ish help page listing arguments and possible sub-commands."""
        width = self.width()

        # Output the summary information.
        for i, spec in enumerate(self.stack):
            summary, description = spec.doc or (None, None)

            if not i:
                if summary: print(wrap(summary, width))
                print("Usage:", os.path.basename(sys.argv[0]), end=" ")

            else:
                print(spec.callable.__name__, end=" ")

            if spec.named:
                print("[CMDOPTS]" if i else "[OPTIONS]", end=" ")

            if spec.keyed:
                print("[--name=value...]", end=" ")

            for arg in spec.positional:
                print("<", arg, ">", sep="", end=" ")

            if spec.indexed:
                print("[value...]", end=" ")

            if spec.cls and len(self.stack) == i + 1:
                print("<COMMAND> ...", end="")

        print()

        # Output the details.
        for i, spec in enumerate(self.stack):
            summary, description = spec.doc or (None, None)

            if i:
                print("\nCommand:", spec.callable.__name__)
                if summary: print(wrap(summary, width))

            if spec.named:
                print("\n", "CMDOPTS" if i else "OPTIONS", " may be one or more of:", sep="", end="\n\n")

                strings = dict()
                abbreviation = dict(zip(spec.short.values(), spec.short.keys()))
                pretty = dict(zip(spec.trans.values(), spec.trans.keys()))

                for name in spec.named:
                    default = spec.defaults.get(name)

                    if spec.cast.get(name, None) is boolean:
                        strings[(("-" + abbreviation[name] + ", ") if name in abbreviation else "") + "--" + pretty.get(name, name)] = \
                                spec.docs.get(name, "Toggle this value.\nDefault: %r" % default)
                        continue

                    strings["-" + abbreviation[name] + ", --" + pretty.get(name, name) + "=VAL"] = \
                            spec.docs.get(name, "Override this value.\nDefault: %r" % default)

                mlen = max([len(j) for j in strings])
                for name in sorted(strings):
                    print(" %-*s  %s" % (mlen, name, wrap(strings[name], width).replace("\n", "\n" + " " * (mlen + 3))))

            if spec.cls and len(self.stack) == i + 1:
                print("\n", "COMMAND may be one of:", sep="", end="\n\n")

                cmds = dict()
                for cmd in dir(spec.target):
                    if cmd[0] == '_' or not callable(getattr(spec.target, cmd)): continue
                    cmds[cmd] = partitionhelp(getdoc(getattr(spec.target, cmd)) or "Undocumented command.")[0]

                mlen = max([len(i) for i in cmds])
                for name in sorted(cmds):
                    print(" %-*s  %s" % (mlen, name, wrap(cmds[name], width).replace("\n", "\n" + " " * (mlen + 3))))

                print("\n", wrap("For help on a specific command, call the command and pass --help in CMDOPTS.", width), sep="")

            if description: print("\n", wrap(description, width), sep="")

        print()

        raise ExitException(os.EX_USAGE, None)

    def version(self, value, via):
        """Attempt to determine the owning package, version, author, and copyright information."""
        pass
    
    @staticmethod
    def width(fallback=79):
        """Return the width of the current terminal, or the fallback value."""

        width = fallback

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

        return width

    def expand(self, arguments, via):
        """Expand short arguments into long ones and expand equations.

        Silently ignores unknown arguments to allow repeated calling for sub-commands.

        `arguments`:
            a list of arguments
        `via`:
            the specification we are expanding from

        You can override this in a subclass to perform additional transformations if you wish.
        """

        result = []

        for arg in arguments:
            # Ensure arguments are unicode.
            # arg = arg.decode(encoding) if isinstance(arg, binary) else arg

            # Skip the impossibility of empty arguments.
            if not arg: continue

            # A double-hyphen argument signals the end of hyphenated arguments.
            if arg == '--' or '--' in result:
                result.append(arg)
                continue

            # Now we start looking for our hyphenated options.
            if len(arg) >= 2 and arg[0] == '-':
                if arg[1] == '-':
                    # This is a long-form argument.
                    name, _, value = arg.partition('=')

                    # We append the name, then value if one exists.
                    result.append(name)
                    if value: result.append(value)

                    continue

                # Expand short arguments into long ones.
                for char in arg[1:]:
                    name = via.short.get(char, None)
                    if name: result.append('--' + name)
                    else: result.append('-' + char)

                continue

            # Other values we just pass along.
            result.append(arg)

        return result

    def arguments(self, arguments, via):
        """Process the given command-line arguments and return the positional, keyword, and remaining arguments.

        Expects long-form arguments only, thus the output of the self.expand method.
        """
        
        remainder = []
        arguments = arguments[::-1]  # We reverse the argument list as popping is more efficient from the end.
        parsing = True
        args = []
        kwargs = {}

        while arguments:
            arg = arguments.pop()

            if arg == '--':
                # Stop processing keyword arguments.
                parsing = False
                continue
            
            if not parsing or ( arg[:2] != '--' and len(args) < via.range[1] ):
                # Positional argument.
                args.append(self.transform(
                        name=via.positional[len(args)] if len(args) < len(via.positional) else None,
                        value=arg,
                        via=via
                    ))
                continue

            if (arg[0] == '-' and arg[1] != '-') or \
                    (arg[:2] == '--' and (via.trans.get(arg[2:], arg[2:]) not in via.named and not via.keyed)) or \
                    (arg[:2] != '--' and len(args) == via.range[1]):
                # Unknown keyword argument or too many positional arguments, exiting early.
                remainder.append(arg)
                remainder.extend(reversed(arguments))
                break

            # Keyword argument.
            arg = arg[2:]

            if via.cast.get(arg, None) is boolean:
                kwargs[arg] = self.transform(name=arg, value=not via.defaults.get(arg, False), via=via)
                continue

            kwargs[arg] = self.transform(name=arg, value=arguments.pop(), via=via)

        return args, kwargs, remainder

    def transform(self, name, value, via):
        """Typecast and optionally utilize callbacks for the given argument."""

        if name is None:
            return value

        cast = via.cast.get(name)
        value = cast(value) if cast else value

        callback = via.callbacks.get(name)
        if callback:
            callback(value, via)

        return value

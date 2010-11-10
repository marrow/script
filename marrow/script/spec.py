# encoding: utf-8

from __future__ import with_statement

import os
import sys
import types
import inspect

from marrow.script.util import *
from marrow.util.object import NoDefault
from marrow.util.convert import boolean, array



class Parser(object):
    def __init__(self, callable):
        self.callable = callable
    
    def process(self, argv, arguments, keywords, types):
        """Returns a dictionary of processed values and a list of unprocessed."""
        
        args = list(arguments)
        args.reverse()
        values = dict(keywords) # default, then override
        remaining = []
        seen = []
        
        state = None
        
        for arg in argv:
            if arg.startswith('--'):
                name, _, value = arg[2:].partition('=')
                
                if name in seen:
                    raise ValueError
                
                if not value and types.get(name, None) in (bool, boolean):
                    values[name] = not values.get(name, False)
                    seen.append(name)
                    if name in args: args.remove(name)
                    continue
                
                if not value:
                    state = name
                    continue
                
                values[name] = types.get(name, str)(value)
                seen.append(name)
                continue
                
            if state:
                values[state] = types.get(name, str)(arg)
                seen.append(state)
                state = None
                continue
            
            if args:
                name = args.pop()
                # if name in keywords:
                #     remaining.append(name)
                #     continue
                
                if name in seen:
                    raise ValueError
                
                seen.append(name)
                values[name] = types.get(name, str)(arg)
                continue
            
            remaining.append(arg)
        
        return values, remaining
    
    def __call__(self, argv):
        cls = None
        callee = self.callable
        
        if inspect.isclass(callee):
            # We need to pre-process and separate out __init__'s arguments.
            cls = callee
            callee = cls()
            pass
        
        arguments, keywords, args, kwargs = getargspec(callee)
        descriptions = getattr(callee, '_cmd_arg_doc', dict())
        types = getattr(callee, '_cmd_arg_types', dict())
        args_range = getattr(callee, '_min_args', len(arguments) - len(keywords)), getattr(callee, '_max_args', len(arguments) - len(keywords))
        
        for name, value in keywords.iteritems():
            if name not in types:
                if isinstance(value, bool):
                    types[name] = boolean
                
                elif isinstance(value, (list, tuple)):
                    types[name] = array
                
                elif value is not None:
                    types[name] = type(value)
        
        values, remaining = self.process(argv, arguments, keywords, types)
        complete = len([i for i in values if i in arguments]) == len(arguments)
        
        if '--help' in argv or '-h' in argv or not complete:
            return self.help(callee, arguments, keywords, descriptions, types, args, kwargs)
        
        if '--version' in argv or '-V' in argv:
            return self.version(callee, arguments, keywords, descriptions, types, args, kwargs)
        
        return callee(*remaining, **values)
    
    def partitionhelp(self, s):
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
    
    def help(self, callee, arguments, keywords, docs, types, args, kwargs):
        doc, doc2 = self.partitionhelp(getattr(callee, '__doc__', None))
        if doc: print wrap(doc)
        
        print 'Usage:', sys.argv[0], '[OPTIONS]',
        
        for arg in arguments:
            if arg in keywords: continue
            print '<%s>' % arg,
        
        keywords = dict(keywords)
        docs = dict(docs)
        
        keywords['help'], types['help'], docs['help'] = None, None, "Display this help and exit."
        keywords['version'], types['version'], docs['version'] = None, None, "Show version and copyright information, then exit."
        
        if keywords:
            print "\n\nOPTIONS may be one or more of:\n"
            help = dict()
            
            for name, default in keywords.iteritems():
                if types.get(name, None) in [bool, boolean]:
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
        
        
        
    
    def version(self, callee, arguments, keywords, docs, types, args, kwargs):
        pass


if __name__ == '__main__':
    def dir(path, verbose=False, cool=[]):
        """Get a directory listing, similar
        to the UNIX `ls` command.
        
        Lorem ipsum dolor sit amet, consectetur adipiscing elit.
        Phasellus et neque libero, non volutpat odio. Mauris eu
        risus tellus, quis vestibulum dolor. Vestibulum orci
        leo, laoreet nec placerat id, tincidunt volutpat nunc.
        
        Aliquam erat volutpat. Curabitur vel rutrum massa. Sed
        eleifend ultrices urna at scelerisque. Ut fringilla
        ipsum eu metus iaculis ut mollis felis dignissim.
        Praesent rutrum, magna non commodo facilisis, justo elit
        iaculis ipsum, at eleifend nunc ante et ante. Praesent
        fringilla urna vel leo vestibulum nec lobortis tortor
        consequat. Duis et tristique lectus. In consequat auctor
        lorem sed hendrerit. Quisque porta vulputate lobortis.
        
        Nulla facilisi. Sed condimentum bibendum accumsan. Morbi
        tristique nisi et urna malesuada at porttitor nisl
        egestas.
        """
        listing = sorted(os.listdir(path))
        
        if not verbose:
            for item in listing:
                print item, '\t',
            
            print "\n\nItems in folder: %d" % (len(listing))
            return 0
        
        for item in listing:
            st_mode, st_ino, st_dev, st_nlink, st_uid, st_gid, st_size, st_atime, st_mtime, st_ctime = os.stat(os.path.join(path, item))
            print item, ' ' * (40-len(item)), st_mtime
    
    command = Parser(dir)
    
    sys.exit(command(sys.argv[1:]))

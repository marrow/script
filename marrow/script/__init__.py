# encoding: utf-8

import sys

from marrow.script.core import Parser


__all__ = ['Parser', 'execute', 'script', 'annotate', 'describe', 'short']



def execute(obj): # pragma: no cover
    sys.exit(Parser(obj)(sys.argv[1:]))



def base(attr):
    def decorator(**kw):
        def inner(fn):
            if not hasattr(fn, attr):
                fn.__dict__[attr] = dict()
            
            fn.__dict__[attr].update(kw)
            
            return fn
        
        return inner
    
    return decorator


script = base('_cmd_script_info')
annotate = base('_cmd_arg_type')
describe = base('_cmd_arg_doc')
short = base('_cmd_arg_abbrev')
callbacks = base('_cmd_arg_callback')

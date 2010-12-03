# encoding: utf-8

from __future__ import unicode_literals

import sys
import types
import inspect

from textwrap import wrap as wrap_


__all__ = ['wrap', 'InspectionComplete', 'InspectionFailed', 'getargspec', 'partitionhelp']


def wrap(text, columns=78):
    lines = []
    
    if isinstance(text, list):
        in_paragraph = False
        for line in text:
            if not line:
                in_paragraph = False
                lines.append(line)
                continue
            
            if in_paragraph:
                lines[-1] = lines[-1] + ' ' + line
                continue
            
            lines.append(line)
            in_paragraph = True
        
        text = "\n".join(lines)
        lines = []
    
    in_paragraph = True
    for iline in text.splitlines():
        if not iline:
            lines.append(iline)
        else:
            for oline in wrap_(iline, columns):
                lines.append(oline)
    
    return "\n".join(lines)


class InspectionComplete(Exception):
    pass


class InspectionFailed(Exception):
    pass


def getargspec(obj):
    """An improved inspect.getargspec.
    
    Has a slightly different return value from the default getargspec.
    
    Returns a tuple of:
        required, optional, args, kwargs
        list, dict, bool, bool
    
    Required is a list of required named arguments.
    Optional is a dictionary mapping optional arguments to defaults.
    Args and kwargs are True for the respective unlimited argument type.
    """
    
    argnames, varargs, varkw, _defaults = None, None, None, None
    
    if inspect.isfunction(obj) or inspect.ismethod(obj):
        argnames, varargs, varkw, _defaults = inspect.getargspec(obj)
    
    elif inspect.isclass(obj):
        if inspect.ismethoddescriptor(obj.__init__):
            argnames, varargs, varkw, _defaults = [], False, False, None
        
        else:
            argnames, varargs, varkw, _defaults = inspect.getargspec(obj.__init__)
    
    elif hasattr(obj, '__call__'):
        argnames, varargs, varkw, _defaults = inspect.getargspec(obj.__call__)
    
    else:
        raise TypeError("Object not callable?")
    
    # Need test case to prove this is even possible.
    # if (argnames, varargs, varkw, defaults) is (None, None, None, None):
    #     raise InspectionFailed()
    
    if argnames and argnames[0] == 'self':
        del argnames[0]
    
    if _defaults is None:
        _defaults = []
        defaults = dict()
    
    else:
        # Create a mapping dictionary of defaults; this is slightly more useful.
        defaults = dict()
        _defaults = list(_defaults)
        _defaults.reverse()
        argnames.reverse()
        for i, default in enumerate(_defaults):
            defaults[argnames[i]] = default
    
        argnames.reverse()
        # del argnames[-len(_defaults):]
    
    return argnames, defaults, True if varargs else False, True if varkw else False


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
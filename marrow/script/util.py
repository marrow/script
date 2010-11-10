# encoding: utf-8

import sys
import types
import inspect

from textwrap import wrap as wrap_


__all__ = ['wrap', 'InspectionComplete', 'InspectionFailed', 'getargspec']


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


def getargspec(obj, nested=False):
    """An improved inspect.getargspec.
    
    Has a slightly different return value from the default getargspec.
    
    Returns a tuple of:
        required, optional, args, kwargs
        list, dict, bool, bool
    
    Required is a list of required named arguments.
    Optional is a dictionary mapping optional arguments to defaults.
    Args and kwargs are True for the respective unlimited argument type.
    """
    
    if not callable(obj):
        raise TypeError, "%s is not callable" % type(obj)
    
    argnames, varargs, varkw, defaults = None, None, None, None
    
    try:
        if inspect.isfunction(obj):
            raise InspectionComplete(*inspect.getargspec(obj))
        
        if hasattr(obj, 'im_func'):
            spec = list(inspect.getargspec(obj.im_func))
            spec[0] = spec[0][1:]
            raise InspectionComplete(*spec)
        
        if inspect.isclass(obj):
            raise InspectionComplete(*getargspec(obj.__init__, True))
        
        if hasattr(obj, '__call__'):
            raise InspectionComplete(*getargspec(obj.__call__, True))
        
        raise InspectionFailed()
    
    except InspectionComplete, exc:
        argnames, varargs, varkw, _defaults = exc.args
        if nested: return argnames, varargs, varkw, _defaults
    
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

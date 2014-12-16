# encoding: utf-8

from __future__ import unicode_literals


class ExitException(Exception):
    pass


class ScriptError(Exception):
    pass


class MalformedArguments(ScriptError):
    pass

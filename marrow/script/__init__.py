# encoding: utf-8

import sys

from core import Parser


__all__ = ['Parser', 'execute']



def execute(obj):
    sys.exit(Parser(obj)(sys.argv[1:]))
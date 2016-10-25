# encoding: utf-8

from __future__ import print_function


def ultima(required, value=None, name="world", switch=False, age=18, *args, **kw):
    print("Hello {}!".format(name))


if __name__ == '__main__':
    from marrow.script import execute
    execute(ultima)

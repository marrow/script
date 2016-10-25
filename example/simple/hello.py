# encoding: utf-8

from __future__ import print_function

def hello():
    print("Hello world!")


if __name__ == '__main__':
    from marrow.script import execute
    execute(hello)

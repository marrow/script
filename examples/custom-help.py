# encoding: utf-8

def hello():
    print "Hello world!"

def myhelpfunc(obj, spec):
    print "Custom help text."


if __name__ == '__main__':
    import sys
    from marrow.script import Parser

    sys.exit(Parser(hello, help=myhelpfunc)(sys.argv[1:]))

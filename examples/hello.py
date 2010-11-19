# encoding: utf-8

def hello():
    print "Hello world!"


if __name__ == '__main__':
    from marrow.script import execute
    execute(hello)

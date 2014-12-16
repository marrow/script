# encoding: utf-8

def ultima(required, value=None, name="world", switch=False, age=18, *args, **kw):
    print "Hello %s!" % (name, )


if __name__ == '__main__':
    from marrow.script import execute
    execute(ultima)

# encoding: utf-8

import os

from marrow.script import execute



def catalog(path, verbose=False):
    """Get a directory listing, similar
    to the UNIX `ls` command.
    
    Lorem ipsum dolor sit amet, consectetur adipiscing elit.
    Phasellus et neque libero, non volutpat odio. Mauris eu
    risus tellus, quis vestibulum dolor. Vestibulum orci
    leo, laoreet nec placerat id, tincidunt volutpat nunc.
    
    Aliquam erat volutpat. Curabitur vel rutrum massa. Sed
    eleifend ultrices urna at scelerisque. Ut fringilla
    ipsum eu metus iaculis ut mollis felis dignissim.
    Praesent rutrum, magna non commodo facilisis, justo elit
    iaculis ipsum, at eleifend nunc ante et ante. Praesent
    fringilla urna vel leo vestibulum nec lobortis tortor
    consequat. Duis et tristique lectus. In consequat auctor
    lorem sed hendrerit. Quisque porta vulputate lobortis.
    
    Nulla facilisi. Sed condimentum bibendum accumsan. Morbi
    tristique nisi et urna malesuada at porttitor nisl
    egestas.
    """
    listing = sorted(os.listdir(path))
    
    if not verbose:
        for item in listing:
            print item, '\t',
        
        print "\n\nItems in folder: %d" % (len(listing))
        return 0
    
    for item in listing:
        st_mode, st_ino, st_dev, st_nlink, st_uid, st_gid, st_size, st_atime, st_mtime, st_ctime = os.stat(os.path.join(path, item))
        print item, ' ' * (40-len(item)), st_mtime


if __name__ == '__main__':
    execute(catalog)

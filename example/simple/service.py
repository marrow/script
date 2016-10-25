# encoding: utf-8

from __future__ import print_function
from __future__ import unicode_literals

import sys
import logging

from marrow.script import Parser


class Service(object):
    """Example service.
    
    Lorem ipsum dolor sit amet, consectetur adipisicing elit, sed do eiusmod
    tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim
    veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea
    commodo consequat. Duis aute irure dolor in reprehenderit in voluptate
    velit esse cillum dolore eu fugiat nulla pariatur. Excepteur sint occaecat
    cupidatat non proident, sunt in culpa qui officia deserunt mollit anim id
    est laborum.
    """
    
    def __init__(self, verbose=False, quiet=False):
        if verbose and quiet:
            print("Can not set verbose and quiet simultaneously.")
            return 1
        
        logging.basicConfig(level=logging.DEBUG if verbose else logging.WARN if quiet else logging.INFO)
        
        self.log = logging.getLogger(__name__)
        
        self.log.info("Initialized.")
    
    def start(self, config=None, app=None):
        """Pretend to start the service.
        
        Lorem ipsum dolor sit amet, consectetur adipisicing elit, sed do
        eiusmod tempor incididunt ut labore et dolore magna aliqua.
        """
        
        self.log.info("Starting %s from %s configuration%s.",
                app if app else "default application",
                config if config else 'default',
                ' file' if config else '')
    
    def stop(self, config=None):
        self.log.info("Stopping service.")
    
    def restart(self, config=None, app=None):
        self.stop(config)
        self.start(config, app)
    
    def reload(self, config=None):
        self.log.info("Reloading configuration.")


sys.exit(Parser(Service)(sys.argv[1:]))

#!/usr/bin/env python

"""LRWPAdapter.py

LRWP Adapter for the WebKit AppServer and the Xitami Web Server.
Adapted from the CGI Adapter for WebKit.

Created by Jim Madsen 09/27/02
"""

# Set program parameters

webwareDir = None

LRWPappName = 'testing'
LRWPhost = 'localhost'
LRWPport = 81

import os
import sys

from lrwplib import LRWP
from Adapter import Adapter

if not webwareDir:
    webwareDir = os.path.dirname(os.path.dirname(os.getcwd()))
sys.path.insert(1, webwareDir)
webKitDir = os.path.join(webwareDir, 'WebKit')


class LRWPAdapter(Adapter):

    def __init__(self, webKitDir=webKitDir):
        Adapter.__init__(self, webKitDir)
        if sys.platform == 'win32':
            import msvcrt
            msvcrt.setmode(sys.stdout.fileno(), os.O_BINARY)
            msvcrt.setmode(sys.stdin.fileno(), os.O_BINARY)
        # Get Host and Port information for WebKit AppServer
        address = open(os.path.join(self._webKitDir, 'adapter.address')).read()
        self.host, self.port = address.split(':', 1)
        self.port = int(self.port)

    def lrwpConnect(self, LRWPappName, LRWPhost, LRWPport):
        try:
            # Make connection to Xitami
            self.lrwp = LRWP(LRWPappName, LRWPhost, LRWPport)
            self.lrwp.connect()
            print
            print 'Connected to Xitami -- Listening for', LRWPappName
            print
            self.LRWPappName = LRWPappName
        except Exception:
            sys.exit('Could not make proper connection to Xitami')

    def handler(self):
        while 1:
            try:
                # Accept requests
                self.request = self.lrwp.acceptRequest()
                env = self.request.env
                # Read input from request object
                self.myInput = ''
                if 'CONTENT_LENGTH' in env:
                    length = env['CONTENT_LENGTH']
                    self.myInput += self.request.inp.read(length)
                # Fix environment variables
                # due to the way Xitami reports them under LRWP
                scriptName = '/' + self.LRWPappName
                env['SCRIPT_NAME'] = scriptName
                env['REQUEST_URI'] = scriptName + env['PATH_INFO']
                # Transact with the app server
                self.response = self.transactWithAppServer(
                    env, self.myInput, self.host, self.port)
                # Log page handled to the console
                print env['REQUEST_URI']
                # Close request to handle another
                self.request.finish()
            # Capture Ctrl-C... Shutdown will occur on next request handled
            except KeyboardInterrupt:
                print
                print 'Closing connection to Xitami'
                print
                self.lrwp.close()
                sys.exit(' Clean Exit')
            except:
                print 'Error handling requests'

    # Output through request object
    def processResponse(self, data):
        self.request.out.write(data)


def main():
    # Startup LRWP to WebKit interface
    lrwpInterface = LRWPAdapter(webKitDir)
    lrwpInterface.lrwpConnect(LRWPappName, LRWPhost, LRWPport)
    lrwpInterface.handler()


if __name__ == '__main__':
    main()

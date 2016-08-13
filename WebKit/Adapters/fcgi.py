#!/bin/env python

#------------------------------------------------------------------------
#               Copyright (c) 1998 by Total Control Software
#                         All Rights Reserved
#------------------------------------------------------------------------
#
# Module Name:  fcgi.py
#
# Description:  Handles communication with the FastCGI module of the
#               web server without using the FastCGI developers kit, but
#               will also work in a non-FastCGI environment, (straight CGI.)
#               This module was originally fetched from someplace on the
#               Net (I don't remember where and I can't find it now...) and
#               has been significantly modified to fix several bugs, be more
#               readable, more robust at handling large CGI data and return
#               document sizes, and also to fit the model that we had
#               previously used for FastCGI.
#
#     WARNING:  If you don't know what you are doing, don't tinker with this
#               module!
#
# Creation Date:    1/30/98 2:59:04PM
#
# License:      This is free software.  You may use this software for any
#               purpose including modification/redistribution, so long as
#               this header remains intact and that you do not claim any
#               rights of ownership or authorship of this software.  This
#               software has been tested, but no warranty is expressed or
#               implied.
#
#------------------------------------------------------------------------


import os
import sys
import socket
import errno
try:
    from cStringIO import StringIO
except ImportError:
    from StringIO import StringIO
import cgi

# Set various FastCGI constants
# Maximum number of requests that can be handled
FCGI_MAX_REQS = 1
FCGI_MAX_CONNS = 1

# Supported version of the FastCGI protocol
FCGI_VERSION_1 = 1

# Boolean: can this application multiplex connections?
FCGI_MPXS_CONNS = 0

# Record types
FCGI_BEGIN_REQUEST = 1
FCGI_ABORT_REQUEST = 2
FCGI_END_REQUEST   = 3
FCGI_PARAMS        = 4
FCGI_STDIN         = 5
FCGI_STDOUT        = 6
FCGI_STDERR        = 7
FCGI_DATA          = 8
FCGI_GET_VALUES    = 9
FCGI_GET_VALUES_RESULT = 10
FCGI_UNKNOWN_TYPE = 11
FCGI_MAXTYPE = FCGI_UNKNOWN_TYPE

# Types of management records
ManagementTypes = [FCGI_GET_VALUES]

FCGI_NULL_REQUEST_ID = 0

# Masks for flags component of FCGI_BEGIN_REQUEST
FCGI_KEEP_CONN = 1

# Values for role component of FCGI_BEGIN_REQUEST
FCGI_RESPONDER = 1 ; FCGI_AUTHORIZER = 2 ; FCGI_FILTER = 3

# Values for protocolStatus component of FCGI_END_REQUEST
FCGI_REQUEST_COMPLETE = 0  # Request completed nicely
FCGI_CANT_MPX_CONN    = 1  # This app can't multiplex
FCGI_OVERLOADED       = 2  # New request rejected; too busy
FCGI_UNKNOWN_ROLE     = 3  # Role value not known


class FCGIError(Exception):
    """FCGI error."""


class Record(object):
    """Class representing FastCGI records"""

    def __init__(self):
        self.version = FCGI_VERSION_1
        self.recType = FCGI_UNKNOWN_TYPE
        self.reqId = FCGI_NULL_REQUEST_ID
        self.content = ''

    def readRecord(self, sock):
        s = map(ord, sock.recv(8))
        self.version, self.recType, paddingLength = s[0], s[1], s[6]
        self.reqId, contentLength = (s[2] << 8) + s[3], (s[4] << 8) + s[5]
        chunks = []
        missing = contentLength
        while missing > 0:
            data = sock.recv(missing)
            chunks.append(data)
            missing -= len(data)
        self.content = ''.join(chunks)
        if paddingLength:
            sock.recv(paddingLength)

        # Parse the content information
        c = self.content
        if self.recType == FCGI_BEGIN_REQUEST:
            self.role = (ord(c[0]) << 8) + ord(c[1])
            self.flags = ord(c[2])

        elif self.recType == FCGI_UNKNOWN_TYPE:
            self.unknownType = ord(c[0])

        elif self.recType == FCGI_GET_VALUES or self.recType == FCGI_PARAMS:
            self.values = {}
            pos = 0
            while pos < len(c):
                name, value, pos = readPair(c, pos)
                self.values[name] = value
        elif self.recType == FCGI_END_REQUEST:
            b = map(ord, c[0:4])
            self.appStatus = (b[0] << 24) + (b[1] << 16) + (b[2] << 8) + b[3]
            self.protocolStatus = ord(c[4])

    def writeRecord(self, sock):
        content = self.content
        if self.recType == FCGI_BEGIN_REQUEST:
            content = chr(self.role >> 8) + chr(self.role & 255) \
                + chr(self.flags) + 5 * '\000'

        elif self.recType == FCGI_UNKNOWN_TYPE:
            content = chr(self.unknownType) + 7 * '\000'

        elif self.recType == FCGI_GET_VALUES or self.recType == FCGI_PARAMS:
            content = ""
            for i in self.values:
                content += writePair(i, self.values[i])

        elif self.recType == FCGI_END_REQUEST:
            v = self.appStatus
            content = chr((v >> 24) & 255) + chr((v >> 16) & 255) \
                + chr((v >> 8) & 255) + chr(v & 255)
            content += chr(self.protocolStatus) + 3 * '\000'

        cLen = len(content)
        eLen = (cLen + 7) & (0xFFFF - 7)  # align to an 8-byte boundary
        padLen = eLen - cLen

        hdr = [
            self.version,
            self.recType,
            self.reqId >> 8,
            self.reqId & 255,
            cLen >> 8,
            cLen & 255,
            padLen,
            0
        ]
        hdr = ''.join(map(chr, hdr))

        sock.sendall(hdr + content + padLen * '\000')


def readPair(s, pos):
    nameLen = ord(s[pos])
    pos += 1
    if nameLen & 128:
        b = map(ord, s[pos:pos+3])
        pos += 3
        nameLen = ((nameLen & 127) << 24) + (b[0] << 16) + (b[1] << 8) + b[2]
    valueLen = ord(s[pos])
    pos += 1
    if valueLen & 128:
        b = map(ord, s[pos:pos+3])
        pos += 3
        valueLen = ((valueLen & 127) << 24) + (b[0] << 16) + (b[1] << 8) + b[2]
    return (s[pos:pos+nameLen], s[pos+nameLen:pos+nameLen+valueLen],
        pos + nameLen + valueLen)


def writePair(name, value):
    n = len(name)
    if n < 128:
        s = chr(n)
    else:
        s = chr(128 | (n >> 24) & 255) + chr((n >> 16) & 255) \
            + chr((n >> 8) & 255) + chr(n & 255)
    n = len(value)
    if n < 128:
        s += chr(n)
    else:
        s += chr(128 | (n >> 24) & 255) + chr((n >> 16) & 255) \
            + chr((n >> 8) & 255) + chr(n & 255)
    return s + name + value


def HandleManTypes(r, conn):
    if r.recType == FCGI_GET_VALUES:
        r.recType = FCGI_GET_VALUES_RESULT
        v = {}
        vars = {
            'FCGI_MAX_CONNS':  FCGI_MAX_CONNS,
            'FCGI_MAX_REQS':   FCGI_MAX_REQS,
            'FCGI_MPXS_CONNS': FCGI_MPXS_CONNS
        }
        for i in r.values:
            if i in vars:
                v[i] = vars[i]
        r.values = vars
        r.writeRecord(conn)


_isFCGI = True  # assume it is until we find out for sure


def isFCGI():
    global _isFCGI
    return _isFCGI


_init = None
_sock = None


class FCGI(object):

    def __init__(self):
        self.haveFinished = False
        if _init is None:
            _startup()
        if not isFCGI():
            self.haveFinished = True
            self.inp, self.out, self.err, self.env = \
                sys.stdin, sys.stdout, sys.stderr, os.environ
            return

        if 'FCGI_WEB_SERVER_ADDRS' in os.environ:
            good_addrs = os.environ['FCGI_WEB_SERVER_ADDRS'].split(',')
            good_addrs = map(good_addrs.strip())  # remove whitespace
        else:
            good_addrs = None

        self.conn, addr = _sock.accept()
        stdin, data = [], []
        self.env = {}
        self.requestId = 0
        remaining = 1

        self.err = sys.stderr = StringIO()
        self.out = sys.stdout = StringIO()

        # Check if the connection is from a legal address
        if good_addrs is not None and addr not in good_addrs:
            raise FCGIError('Connection from invalid server!')

        while remaining:
            r = Record()
            r.readRecord(self.conn)

            if r.recType in ManagementTypes:
                HandleManTypes(r, self.conn)

            elif r.reqId == 0:
                # Oh, poopy. It's a management record of an unknown type.
                # Signal the error.
                r2 = Record()
                r2.recType = FCGI_UNKNOWN_TYPE
                r2.unknownType = r.recType
                r2.writeRecord(self.conn)
                continue  # charge onwards

            # Ignore requests that aren't active
            elif (r.reqId != self.requestId
                    and r.recType != FCGI_BEGIN_REQUEST):
                continue

            # If we're already doing a request, ignore further BEGIN_REQUESTs
            elif r.recType == FCGI_BEGIN_REQUEST and self.requestId != 0:
                continue

            # Begin a new request
            if r.recType == FCGI_BEGIN_REQUEST:
                self.requestId = r.reqId
                if r.role == FCGI_AUTHORIZER:
                    remaining = 1
                elif r.role == FCGI_RESPONDER:
                    remaining = 2
                elif r.role == FCGI_FILTER:
                    remaining = 3

            elif r.recType == FCGI_PARAMS:
                if r.content == '':
                    remaining -= 1
                else:
                    for i in r.values:
                        self.env[i] = r.values[i]

            elif r.recType == FCGI_STDIN:
                if r.content:
                    stdin.append(r.content)
                else:
                    remaining -= 1

            elif r.recType == FCGI_DATA:
                if r.content:
                    data.append(r.content)
                else:
                    remaining -= 1

        stdin, data = ''.join(stdin), ''.join(data)

        self.inp = sys.stdin = StringIO(stdin)
        self.data = StringIO(data)

    def __del__(self):
        self.Finish()

    def Finish(self, status=0):
        if not self.haveFinished:
            self.haveFinished = True

            self.err.seek(0, 0)
            self.out.seek(0, 0)

            r = Record()
            r.recType = FCGI_STDERR
            r.reqId = self.requestId
            data = self.err.read()
            while data:
                chunk, data = self.getNextChunk(data)
                r.content = chunk
                r.writeRecord(self.conn)
            r.content = ''
            r.writeRecord(self.conn)  # Terminate stream

            r.recType = FCGI_STDOUT
            data = self.out.read()
            while data:
                chunk, data = self.getNextChunk(data)
                r.content = chunk
                r.writeRecord(self.conn)
            r.content = ''
            r.writeRecord(self.conn)  # Terminate stream

            r = Record()
            r.recType = FCGI_END_REQUEST
            r.reqId = self.requestId
            r.appStatus = status
            r.protocolStatus = FCGI_REQUEST_COMPLETE
            r.writeRecord(self.conn)
            self.conn.close()

    def getFieldStorage(self):
        method = 'GET'
        if 'REQUEST_METHOD' in self.env:
            method = self.env['REQUEST_METHOD'].upper()
        return cgi.FieldStorage(fp=self.inp if method != 'GET' else None,
            environ=self.env, keep_blank_values=1)

    def getNextChunk(self, data):
        return data[:8192], data[8192:]


Accept = FCGI  # alias for backwards compatibility


def _startup():
    global _init
    _init = 1
    try:
        s = socket.fromfd(sys.stdin.fileno(),
            socket.AF_INET, socket.SOCK_STREAM)
        s.getpeername()
    except socket.error as err:
        if err.errno != errno.ENOTCONN:  # must be a non-fastCGI environment
            global _isFCGI
            _isFCGI = False
            return

    global _sock
    _sock = s


def _test():
    counter = 0
    try:
        while isFCGI():
            req = Accept()
            counter += 1

            try:
                fs = req.getFieldStorage()
                size = int(fs['size'].value)
                doc = ['*' * size]
            except Exception:
                doc = ['<HTML><HEAD><TITLE>FCGI TestApp</TITLE></HEAD>\n<BODY>\n']
                doc.append('<H2>FCGI TestApp</H2><P>')
                doc.append('<b>request count</b> = %d<br>' % counter)
                doc.append('<b>pid</b> = %s<br>' % os.getpid())
                if 'CONTENT_LENGTH' in req.env:
                    cl = int(req.env['CONTENT_LENGTH'])
                    doc.append('<br><b>POST data (%d):</b><br><pre>' % cl)
                    for k in sorted(fs):
                        val = fs[k]
                        if isinstance(val, list):
                            doc.append('    <b>%-15s :</b>  %s\n' % (k, val))
                        else:
                            doc.append('    <b>%-15s :</b>  %s\n' % (k, val.value))
                    doc.append('</pre>')

                doc.append('<P><HR><P><pre>')
                for k in sorted(req.env):
                    doc.append('<b>%-20s :</b>  %s\n' % (k, req.env[k]))
                doc.append('\n</pre><P><HR>\n')
                doc.append('</BODY></HTML>\n')

            doc = ''.join(doc)
            req.out.write('Content-Length: %s\r\n'
                'Content-Type: text/html\r\n'
                'Cache-Control: no-cache\r\n'
                '\r\n' % len(doc))
            req.out.write(doc)

            req.Finish()
    except Exception:
        import traceback
        with open('traceback', 'w') as f:
            traceback.print_exc(file=f)
            # f.write('%s' % doc)


if __name__ == '__main__':
    # import pdb; pdb.run('_test()')
    _test()

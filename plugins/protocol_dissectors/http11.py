# -*- coding: utf8 -*-
__author__ = 'Richard Chen'

import sys
sys.path.append('../..')

from core.Plugins.ProtocolDissector import *
from cStringIO import StringIO
from contextlib import closing
from gzip import GzipFile

def getClassReference():
    return HTTP11


# Parses HTTP Requests / Responses according to http://tools.ietf.org/html/rfc7230
class HTTP11(ProtocolDissector):
    defaultPorts = [80, 8080, 8000, 443]

    decoders = {
        'gzip':     lambda x: GzipFile(fileobj=StringIO(x)).read(),
        'x-gzip':   lambda x: GzipFile(fileobj=StringIO(x)).read(),
        'deflate':  lambda x: x.decode('zlib'),
    }

    protocolName = "HTTP 1.1"

    @classmethod
    def getRequestPayload(cls, data):
        return cls.getResponsePayload(data)     # No special case found yet that has to be handled differently

    @classmethod
    def decode(cls, payload, encoding):
        if not payload:
            return None

        if encoding not in cls.decoders.keys():
            return payload

        try:
            return cls.decoders[encoding](payload)
        except Exception as e:
            return payload

    @classmethod
    def getResponsePayload(cls, data):
        payload = '' 
        encoding = None
        headers = cls.parseHeaders(data)
        if 'Content-Length' in headers:
            length = int(headers['Content-Length'])
            payload = data.read(length)

        if 'Content-Encoding' in headers:
            encoding = headers['Content-Encoding']
            encoding = encoding.split(':')[-1].strip().lower()

        if 'Transfer-Encoding' in headers:
            encoding = headers['Transfer-Encoding']
            encoding = encoding.split(':')[-1].strip().lower()
            if 'chunked' in encoding:
                # Decode chunked data
                length = 1
                while length: 
                    length = int(data.readline()[:-2],16)
                    payload += data.read(length)
                    lineend = data.read(2)
                    assert lineend == "\r\n"
        return (headers,cls.decode(payload, encoding))

    @classmethod
    def parseHeaders(cls, data):
        headers = dict()
        line = data.readline()
        while line not in ['\r\n','']:
            keyval = line.split(':')
            try:
                headers[keyval[0].strip()] = keyval[1].strip()
            except:
                sys.exit()
            line = data.readline()
        return headers

    @classmethod
    def parseData(cls, data):
        with closing(StringIO(data)) as data:
            # check start line for HTTP 1.1 tag
            line = data.readline()
            if 'HTTP/1.1' not in line:
                return None

            packets = []

            #loop to allow HTTP pipelining
            while line != '':
                # classify as Request or Response
                if line.startswith('HTTP'):
                    headers,payload = cls.getResponsePayload(data)
                    assert(len(packets)>0)
                    packets[-1]['response']['headers'] = headers
                    packets[-1]['response']['payload'] = payload
                else:
                    packetinfo = {'request':{},'response':{}} 
                    headers,payload = cls.getRequestPayload(data)
                    packetinfo['request']['payload'] = payload
                    packetinfo['request']['headers'] = headers
                    try:
                        packetinfo['response']['filename'] = cls.getFilename(line)
                    except:
                        packetinfo['response']['filename'] = 'Untitled File'
                    packetinfo['response']['headers'] = None
                    packetinfo['response']['payload'] = None
                    packets.append(packetinfo)
                #if payload:
                #    cls.packets.append(packetinfo)

                line = data.readline()
            return packets

    @classmethod
    def getFilename(cls,line):
        # Get Filename in HTTP Request
        filename = line.split(' ')[1]
        filename = filename.split('?')[0].split('/')[-1]
        return filename








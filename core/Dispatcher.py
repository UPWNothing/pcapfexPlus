# -*- coding: utf8 -*-
__author__ = 'Viktor Winkelmann'

import multiprocessing
from ThreadPool.Pool import Pool
from Files.FileManager import *
from Files.FileObject import *
from Streams.StreamBuilder import *
from Plugins.PluginManager import *
from time import time

DEBUG = True

class Dispatcher:
    def __init__(self, pcapfile, outputdir='output', entropy=False, **kwargs):
        self.kwargs = kwargs
        self.pcapfile = pcapfile
        self.filemanager = FileManager(outputdir)
        self.pm = PluginManager()
        self.outputdir = outputdir
        self.useEntropy = entropy
        self.countfiles = 0

    def _finishedSearch(self, (stream, result)):
        Utils.printl("Found %d files in %s stream %s" % (len(result), stream.protocol, stream.infos))
        self.countfiles += len(result)
        map(self.filemanager.addFile, result)

    def run(self):
        self.outputdir += str(time())
        if os.path.exists(self.outputdir):
            print "Output folder \'%s\' already exists! Exiting..." % (self.outputdir,)
            self.filemanager.exit()
            return


        print "Reassembling streams..."
        streambuilder = StreamBuilder(self.pcapfile, **self.kwargs)
        allstreams = streambuilder.tcpStreams + streambuilder.udpStreams

        print "\nStream Reassembly finished.\n\tFile %s has a total of %d single-direction streams." % (self.pcapfile,
                                                                                                   len(allstreams))

        print "Searching streams for forensic evidence...\n"
        if DEBUG:
            # Single threaded search for easier debugging
            map(lambda s: self._finishedSearch(self._findFiles(s)), allstreams)
        else:
            # Multi threaded search as standard
            workers = Pool(multiprocessing.cpu_count())
            workers.map_async(self._findFiles, allstreams, self._finishedSearch)
            workers.join()



        self.filemanager.exit()
        print "Evidence search has finished.\n"
        print "{0} files found.".format(self.countfiles)


    def _findFiles(self, stream):
        files = []
        packets= []
        streamdata = stream.getAllBytes()
        streamPorts = (stream.ipSrc, stream.ipDst)

        for protocol in self.pm.getProtocolsByHeuristics(streamPorts):
            packets = self.pm.protocolDissectors[protocol].parseData(streamdata)
            if packets is not None:
                stream.protocol = self.pm.protocolDissectors[protocol].protocolName
                break

        for packet in packets:
            if stream.protocol == 'HTTP 1.1':
                if packet['response']['payload'] and packet['response']['filename']:
                    file = FileObject(packet['response']['payload'])
                    file.source = stream.ipSrc
                    file.destination = stream.ipDst
                    file.filename = packet['response']['filename']
                if stream.tsFirstPacket:
                    file.timestamp = stream.tsFirstPacket
                files.append(file)
                
                if packet['request']['payload']:
                    packet = packet['request']['payload']
                else:
                    continue

            if packet is None:
                continue
            # No payload in Request-Response pair
            #if packet['response']['payload'] is None and packet['request']['payload'] is None:
            #    continue
            
            for decoder in self.pm.decoders:
                payload = self.pm.decoders[decoder].decodeData(packet)
                if payload is None:
                    continue

                for datarecognizer in self.pm.dataRecognizers:
                    for occ in self.pm.dataRecognizers[datarecognizer].findAllOccurences(payload):
                        file = FileObject(payload[occ[0]:occ[1]])
                        file.source = stream.ipSrc
                        file.destination = stream.ipDst
                        file.fileEnding = self.pm.dataRecognizers[datarecognizer].fileEnding
                        file.type = self.pm.dataRecognizers[datarecognizer].dataCategory
                        if stream.tsFirstPacket:
                            file.timestamp = stream.tsFirstPacket
                        files.append(file)

                if self.useEntropy:
                    type = self.pm.entropyClassifier.classify(payload)
                    file = FileObject(payload)
                    file.source = stream.ipSrc
                    file.destination = stream.ipDst
                    file.type = type
                    if stream.tsFirstPacket:
                        file.timestamp = stream.tsFirstPacket
                    files.append(file)
                    

        return (stream, files)

if __name__ == '__main__':
    d = Dispatcher(os.path.dirname(__file__) + '/../tests/webextract/web_light.pcap')
    d.run()

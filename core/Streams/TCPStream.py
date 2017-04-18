# -*- coding: utf8 -*-
__author__ = 'Viktor Winkelmann'

from cStringIO import StringIO
from contextlib import closing
from PacketStream import *
import dpkt

class TCPStream(PacketStream):
    def __init__(self, ipSrc, portSrc, ipDst, portDst):
        PacketStream.__init__(self, ipSrc, portSrc, ipDst, portDst)

        self.packets = dict()
        self.replypackets = dict()

    def __len__(self):
        return len(self.packets)

    def addPacket(self, packet, ts, reply=False):
        if type(packet) != dpkt.tcp.TCP:
            raise TypeError('Packet is not a TCP packet!')

        if len(packet.data) == 0:
            return

        if not reply:
            if packet.seq not in self.packets or len(self.packets[packet.seq].data) < len(packet.data):
                self.packets[packet.seq] = packet
        else: 
            if packet.seq not in self.replypackets or len(self.replypackets[packet.seq].data) < len(packet.data):
                self.replypackets[packet.seq] = packet

        if self.tsFirstPacket is None or ts < self.tsFirstPacket:
            self.tsFirstPacket = ts

        if self.tsLastPacket is None or ts > self.tsLastPacket:
            self.tsLastPacket = ts


    def __iter__(self):
        sortedPackets = self.merge()
        for packet in sortedPackets:
            yield packet

    def getFirstBytes(self, count):
        with closing(StringIO()) as bytes:
            index = 0
            #sortedPackets = sorted(self.packets.values(), key=lambda v: v.seq)
            sortedPackets = self.merge()
            while len(bytes) < count and index < len(sortedPackets):
                bytes.write(sortedPackets[index].data)
                index += 1

            return bytes.getvalue()[:count]

    def getAllBytes(self):
        with closing(StringIO()) as bytes:
            for packet in self:
                bytes.write(packet.data)

            return bytes.getvalue()

    def isValid(self):
        if len(self.packets) == 0 or len(self.replypackets) == 0:
            return False
        
        sortedPackets = sorted(self.packets.values(), key=lambda v: v.seq)
        sortedReplyPackets = sorted(self.replypackets.values(), key=lambda v:v.seq)
        firstPacket = sortedPackets[0]
        secondPacket = sortedReplyPackets[0]

        if len(firstPacket.data) == 0:
            nextSeq += 1
        else:
            nextSeq = firstPacket.seq + len(firstPacket.data)

        if secondPacket.ack != nextSeq:
            return False

        for packet in sortedPackets[1:]:
            if packet.seq != nextSeq:
                return False

            if len(packet.data) == 0:
                nextSeq += 1
            else:
                nextSeq += len(packet.data)

        nextSeq = secondPacket.seq
        for packet in sortedReplyPackets:
            if packet.seq != nextSeq:
                return False

            if len(packet.data) == 0:
                nextSeq += 1
            else:
                nextSeq += len(packet.data)

        return True

    def merge(self):
        sortedReplyPackets = sorted(self.replypackets.values(), key=lambda v:v.seq)
        sortedPackets = sorted(self.packets.values(), key=lambda v: v.seq)
        mergedPackets = []
        mergedPackets.append(sortedPackets[0])
        mergedPackets.append(sortedReplyPackets[0])
        reply = True
        i=1
        j=1
        while i < len(sortedPackets) and j < len(sortedReplyPackets):
            if reply:
                if sortedPackets[i].ack > sortedReplyPackets[j].seq:
                    mergedPackets.append(sortedReplyPackets[j])
                    j+=1
                else:
                    mergedPackets.append(sortedPackets[i])
                    i+=1
                    reply = False
            else:
                if sortedReplyPackets[j].ack > sortedPackets[i].seq:
                    mergedPackets.append(sortedPackets[i])
                    i+=1
                else:
                    mergedPackets.append(sortedReplyPackets[j])
                    j+=1
                    reply = True
        for k in range(i,len(sortedPackets)):
            mergedPackets.append(sortedPackets[k])
        for k in range(j,len(sortedReplyPackets)):
            mergedPackets.append(sortedReplyPackets[k])
        return mergedPackets
    
    # For Test
    def printall(self,packets):
        print "SrcIP:{}\tDstIP:{}\tSrcPort:{}\tDstPort:{}".format(self.ipSrc,self.ipDst,self.portSrc,self.portDst)
        for packet in packets:
            print "{} --> {} SEQ:{} ACK:{}".format(packet.sport,packet.dport,packet.seq,packet.ack)
            

#probe.py
from twisted.internet.protocol import ClientFactory, Protocol
from twisted.internet import reactor
import json
from common import *
from zope.interface import implements
from twisted.internet.interfaces import IConsumer
from twisted.internet.defer import Deferred

EVENT_CODES={
    0:'FILES_LISTED',
    2:'FILE_RECIEVED'
}
class FileReciever(object):
    implements(IConsumer)

    def __init__(self, fObj, callbackListing):
        self.fObj = fObj
        self.returningFn=callbackListing

    def registerProducer(self, producer, streaming):
        self.producer = producer

    def unregisterProducer(self):
        print 'done'
        self.producer = None
        self.fObj.close()
        self.returningFn(True)


    def write(self, bytes):
        self.fObj.write(bytes)

class FileDiscovery(Protocol):
    def connectionMade(self):
        self.sendLine()


class ProbeFactory(ClientFactory):
    def __init__(self, callback):
        self.callback=callback

    def startedConnecting(self, connector):
        print 'Started to connect.'

    def buildProtocol(self, addr):
        return Probe(self.callback)

if __name__ == '__main__':
    # connect factory to this host and port
    def cbFn(probe):
        # print probe.fileHT
        fileHash=raw_input('enter hash: ')
        f=open('temp_file','wb')
        return (fileHash,f)
    reactor.connectTCP(raw_input('IP: '), 17395, ProbeFactory(cbFn))
    reactor.run()

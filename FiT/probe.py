#probe.py
from twisted.internet.protocol import Factory
from twisted.protocols.basic import LineReceiver, FileSender
from twisted.internet import reactor
import json
from common import *
from zope.interface import implements
from twisted.internet.interfaces import IConsumer

CLIENT_STATES={
    0:'NOT_LISTED',
    1:'FILE_TRANSFER'
    2:'BUSY'
}

EVENT_CODES={
    0:'FILES_LISTED',
    2:'FILE_RECIEVED'
}

class FileReciever(object):
    implements(IConsumer)

    def __init__(self, fObj):
        self.fObj = fObj
        self.cbTrigger=function

    def registerProducer(self, producer, streaming):
        self.producer = producer

    def unregisterProducer(self):
        self.producer = None
        self.fObj.close()
        self.cbTrigger(True)

    def write(self, bytes):
        self.fObj.write(bytes)


class Probe(LineReceiver):
    def __init__(self, callbackListing, callbackComplete):
        self.fileHT={}
        self.state = 1
        self.STATE_FUNCTIONS={
            1:self._file_listing,
            2:self._do_nothing}
        self._event_functions={
            0:callbackListing,
            2:callbackComplete}

    def connectionMade(self):
        self.sendLine(str(self.ident))

    def connectionLost(self, reason):
        pass

    def lineReceived(self, line):
        if not self.STATE_FUNCTIONS[self.state](line):
            self.transport.loseConnection()

    def _file_listing(self, json_str):
        try:
            self.fileHT=json.loads(json_str)
            callingFn=self._event_functions[self.state]
            if not callingFn is None:

            return True
        except Exception as e:
            print e
            return False        

    def _do_nothing(self, _):
        return True

    def complete_transfer(self, success):
        if not success:
            

class ProbeFactory(Factory):
    def __init__(self):
        pass

    def buildProtocol(self, addr):
        return Probe()

if __name__ == '__main__':
    # connect factory to this host and port
    point = TCP4ClientEndpoint(reactor, raw_input('Dest. IP: '), 17395)
    point.connect(ProbeFactory(i))
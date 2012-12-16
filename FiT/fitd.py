from twisted.internet.protocol import Factory
from twisted.protocols.basic import LineReceiver, FileSender
from twisted.internet import reactor
import json
from common import *
from indexer import *

SERVER_STATES={
    1:'FILE_TRANSFER',
    2:'BUSY'
}



class FileTransferDaemon(LineReceiver):
    def __init__(self, file_indexer):
        self.STATE_FUNCTIONS={
            1:self.transfer_file,
            2:self.do_nothing}
        self.indexer=file_indexer
        self.rFn=None
        self.state = 1

    def addRefreshTrigger(self, refreshFn):
        self.rFn=refreshFn

    def connectionMade(self):
        self.sendLine(json.dumps(self.indexer.index))

    def connectionLost(self, reason):
        pass

    def lineReceived(self, line):
        if not self.STATE_FUNCTIONS[self.state](line):
            self.transport.loseConnection()
        
    def transfer_file(self, fileHash):
        if not fileHash in self.indexer.index:
            self.sendLine('INVALID_FILE_ID')
            return False
        file_obj=self.indexer.getFile(fileHash)
        self.sendLine('SUCCESS_F_S')
        self.state=2
        #Simulates a Producer; transport - underlying protocol; is the consumer
        fs=FileSender()
        self.transport.registerProducer(fs, streaming=False)
        d=fs.beginFileTransfer(file_obj, self.transport)
        #Add completion triggers
        d.addCallback(self.complete_transfer, True)
        d.addErrback(self.complete_transfer, False)
        return True

    def do_nothing(self, _):
        return True

    def complete_transfer(self, success):
        self.state=1
        if not success:
            self.transport.loseConnection()

class IFFactory(Factory):
    def __init__(self, indexer):
        self.inx=indexer

    def buildProtocol(self, addr):
        return FileTransferDaemon(self.inx)

if __name__ == '__main__':
    reactor.listenTCP(17395, IFFactory(FileIndexer('/home/vasuman/Downloads')))
    reactor.run()
from twisted.internet.protocol import Factory, Protocol
from twisted.protocols.basic import FileSender
from twisted.internet import reactor
import json
from common import *
from indexer import *


class FileTransferDaemon(Protocol):
    def __init__(self, file_indexer):
        self.busy=False
        self.err_count=0
        self.indexer=file_indexer
        self.fileObj=None
        self.request_handler={
            1:self._dump_file_HT,
            2:self._load_file,
            3:self._start_transfer,
            }

    def sendLine(self, line):
        self.transport.write(str(line)+'\n')

    def dataReceived(self, buff_str):
        for char in buff_str:
            self.buffLine+=char
            if char =='\n':
                self.serviceRequest(self.buffLine[:-1])
                self.buffLine=''

    def serviceRequest(self, request):
        if self.busy: return
        try:
            req=m.LMessage(message_str=request)
            self.request_handler[req.code](req.data)
        except Exception as e:
            self._failure()
            self.sendLine(DaemonException(1,'Invalid request'))

    def _load_file(self, fileHash):
        try:
            self.fileObj=self.indexer.getFile(fileHash)
        except IndexerException as e:
            self.sendLine(e)

    def _start_transfer(self, _discard):
        self.busy=True

    def _failure(self):
        self.err_count+=1
        if self.err_count > 3:
            self.transport.loseConnection()

    def _dump_file_HT(self):
        self.sendLine(self.indexer.reduced_index())
        
class IFFactory(Factory):
    def __init__(self, indexer):
        self.inx=indexer

    def buildProtocol(self, addr):
        return FileTransferDaemon(self.inx)

if __name__ == '__main__':
    reactor.listenTCP(17395, IFFactory(FileIndexer('/home/vasuman/Downloads')))
    reactor.run()
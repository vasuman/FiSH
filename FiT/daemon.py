from twisted.internet.protocol import Factory, Protocol
from twisted.protocols.basic import FileSender
from twisted.internet import reactor
import json
from common import *
from indexer import *


class FileShareDaemon(StreamLineProtocol):
    def __init__(self, file_indexer):
        StreamLineProtocol.__init__(self)
        self.busy=False
        self.err_count=0
        self.indexer=file_indexer
        self.fileObj=None
        self.request_handler={
            1:self._dump_file_HT,
            2:self._load_file,
            3:self._start_transfer,
        }

    def serviceMessage(self, request):
        if self.busy: return
        try:
            req=LMessage(message_str=request)
            self.request_handler[req.key](req.data)
        except Exception as e:
            self._failure((1,'INVALID_REQUEST'))

    def _dump_file_HT(self, _discard):
        self.sendLine(self.indexer.reduced_index())
    
    def _load_file(self, fileMsg):
        try:
            fileHash=fileMsg[0][0]
            self.fileObj=self.indexer.getFile(fileHash)
            file_size=self.indexer.getFileSize(fileHash)
            reply_msg=LMessage(3,[(file_size,)])
            self.sendLine(reply_msg)
        except IndexerException as e:
            self.sendLine(e)

    def _start_transfer(self, _discard):
        if self.fileObj is None:
            self._failure((2,'NO_FILE_LOADED'))
        else:
            self.busy=True
            fileProducer=FileSender()
            def_obj=fileProducer.beginFileTransfer(file=self.fileObj, consumer=self.transport)
            def_obj.addCallback(self._done_transfer, True)
            def_obj.addErrback(self._done_transfer, False)

    def _done_transfer(self, _discard, success):
        self.busy=False
        if not success:
            self._failure((5,'INCOMPLETE_TRANSFER'))

    def _failure(self, reason):
        self.sendLine(LMessage(4,[reason]))
        self.err_count+=1
        if self.err_count > 5:
            error_msg=LMessage(4,[(6,'MAX_ERR')])
            self.sendLine(error_msg)
            self.transport.loseConnection()

        
class IFFactory(Factory):
    def __init__(self, indexer):
        self.inx=indexer

    def buildProtocol(self, addr):
        return FileShareDaemon(self.inx)

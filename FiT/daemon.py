from twisted.internet.protocol import Factory, Protocol
from twisted.protocols.basic import FileSender
from twisted.internet import reactor
import json
from common import *
from indexer import *


class FileTransferDaemon(Protocol):
    def __init__(self, file_indexer):
        self.buffLine=''
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
                cmd_str=self.buffLine.replace('\n','')
                cmd_str=cmd_str.replace('\r','')
                self.serviceRequest(cmd_str)
                self.buffLine=''

    def serviceRequest(self, request):
        if self.busy: return
        try:
            req=LMessage(message_str=request)
            self.request_handler[req.key](req.data)
        except Exception as e:
            print e
            self._failure()
            error_msg=LMessage(4,[(1,'INVALID_REQUEST')])
            self.sendLine(error_msg)

    def _dump_file_HT(self, _discard):
        self.sendLine(self.indexer.reduced_index())
    
    def _load_file(self, fileHL):
        try:
            fileHash=fileHL[0][0]
            self.fileObj=self.indexer.getFile(fileHash)
        except IndexerException as e:
            self.sendLine(e)

    def _start_transfer(self, _discard):
        if self.fileObj is None:
            self._failure()
            error_msg=LMessage(4,[(2,'NO_FILE_LOADED')])
            self.sendLine(error_msg)
            return -1
        self.busy=True
        fs_proc=FileSender()
        d=fs_proc.beginFileTransfer(file=self.fileObj, consumer=self.transport)
        d.addCallback(self._done_transfer, True)
        d.addErrback(self._done_transfer, False)

    def _done_transfer(self, _discard, success):
        self.busy=False
        if not success:
            self._failure()

    def _failure(self):
        self.err_count+=1
        if self.err_count > 5:
            error_msg=LMessage(4,[(5,'MAX_ERR')])
            self.sendLine(error_msg)
            self.transport.loseConnection()

        
class IFFactory(Factory):
    def __init__(self, indexer):
        self.inx=indexer

    def buildProtocol(self, addr):
        return FileTransferDaemon(self.inx)

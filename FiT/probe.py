#probe.py
from twisted.internet.protocol import ClientFactory, Protocol
from twisted.internet import reactor
from twisted.internet.defer import Deferred
import json
from common import *
import logging

EVENT_CODES={
    0:'FILES_LISTED',
    2:'FILE_RECIEVED'
}
        
class HashListRetrieve(StreamLineProtocol):
    def __init__(self):
        StreamLineProtocol.__init__(self)

    def connectionMade(self):
        self.sendLine(FiTMessage(1,[]))

    def serviceMessage(self, message):
        success=True
        fileHT={}
        try:
            fileHT=json.loads(message)
        except:
            logging.error('Invalid JSON recieved from peer')
            success=False
        self.transport.loseConnection()
        self.factory.got_HT(success, fileHT)
  
class FileTransfer(StreamLineProtocol):
    def __init__(self, fileHash, f_container, def_obj):
        StreamLineProtocol.__init__(self)
        self.def_obj=def_obj
        self.fileHash=fileHash
        self.fObj=f_container
        self.retFn=self._FTReply
        self.fGot=0
        self.fSize=0
        self.state=0

    def connectionMade(self):
        self.sendLine(FiTMessage(2,[(self.fileHash,)]))
        self.state=1

    def serviceMessage(self, message):
        self.retFn(message)

    def _FTReply(self, reply):
        try:
            msg=FiTMessage(message_str=reply)
            if msg.key == 4:
                raise Exception(msg.data[0])
            elif msg.key != 3:
                raise Exception('Wrong Code')
        except Exception as e:
            logging.error('Failed to negotiate file transfer')
            self.transport.loseConnection()
            if not self.def_obj is None:
                d, self.def_obj = self.def_obj, None
                d.errback(str(e))
            return
        self.state=2
        self.fSize=int(msg.data[0][0])
        reply_msg=FiTMessage(3,[(str(self.fSize),)])
        StreamLineProtocol.registerSpHandler(self, self.fillFile)
        self.sendLine(reply_msg)

    def fillFile(self, data):
        self.fGot+=len(data)
        self.fObj.write(data)
        if self.fGot >= self.fSize:
            if not self.def_obj is None:
                d, self.def_obj = self.def_obj, None
                d.callback(True)
            logging.info('File Transfer is done')
            self.fObj.close()
            self.transport.loseConnection()
            
            

class FHFactory(ClientFactory):
    protocol=HashListRetrieve
    def __init__(self, def_obj):
        self.def_obj=def_obj

    def got_HT(self, success, fileHT):
        if self.def_obj is not None:
            d, self.def_obj = self.def_obj, None
            if success:    
                d.callback(fileHT)
            else:
                d.errback('Parsing JSON error')

    def clientConnectionFailed(self, connector, reason):
        if self.def_obj is not None:
            d, self.def_obj = self.def_obj, None
            d.errback(reason)

class FTFactory(ClientFactory):
    def __init__(self, fHash, f_container, def_obj):
        self.fHash=fHash
        self.fObj=f_container
        self.def_obj=def_obj
        self.ftInst=None
        
    def buildProtocol(self, addr):
        new_d=Deferred()
        ftInst=FileTransfer(self.fHash, self.fObj, new_d)
        ftInst.factory=self
        if not self.def_obj is None:
            d, self.def_obj = self.def_obj, None
            d.callback(ftInst)
        return ftInst

    def clientConnectionFailed(self, connector, reason):
        if self.def_obj is not None:
            d, self.def_obj = self.def_obj, None
            d.errback(reason)

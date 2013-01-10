#probe.py
from twisted.internet.protocol import ClientFactory, Protocol
from twisted.internet import reactor
import json
from common import *

EVENT_CODES={
    0:'FILES_LISTED',
    2:'FILE_RECIEVED'
}
        
class HashListRetrieve(StreamLineProtocol):
    def __init__(self, callbackListing):
        StreamLineProtocol.__init__(self)
        self.cbFn=callbackListing

    def connectionMade(self):
        self.sendLine(FiTMessage(1,[]))

    def serviceMessage(self, message):
        success=True
        fileHT={}
        try:
            fileHT=json.loads(message)
        except:
            success=False
        self.transport.loseConnection()
        reactor.callInThread(self.cbFn, success, fileHT)
  
class FileTransfer(StreamLineProtocol):
    def __init__(self, fileHash, f_container, callbackListing):
        StreamLineProtocol.__init__(self)
        self.fileHash=fileHash
        self.fObj=f_container
        self.retFn=self._FTReply
        self.cbFn=callbackListing

    def connectionMade(self):
        self.sendLine(FiTMessage(2,[(self.fileHash,)]))

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
            self.transport.loseConnection()
            return
        self.fSize=int(msg.data[0][0])
        reply_msg=FiTMessage(3,[(str(self.fSize),)])
        StreamLineProtocol.registerSpHandler(self, self.fillFile)
        self.sendLine(reply_msg)

    def fillFile(self, data):
        self.fSize-=len(data)
        self.fObj.write(data)
        if self.fSize <= 0:
            self.fObj.close()
            self.transport.loseConnection()
            reactor.callInThread(self.cbFn, True)

class FHFactory(ClientFactory):
    def __init__(self, callback):
        self.callback=callback

    def buildProtocol(self, addr):
        return HashListRetrieve(self.callback)

class FTFactory(ClientFactory):
    def __init__(self, fHash, f_container, cbFn):
        self.fHash=fHash
        self.fObj=f_container
        self.callback=cbFn

    def buildProtocol(self, addr):
        return FileTransfer(self.fHash, self.fObj, self.callback)

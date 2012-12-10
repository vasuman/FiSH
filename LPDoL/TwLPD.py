from twisted.internet.protocol import DatagramProtocol
from twisted.internet import reactor
import socket as sck
from pickle import dumps,loads
from collections import namedtuple, Counter
from message import Message
from common import *
from util import MessageHandler

class Inducter(DatagramProtocol):
    '''The heart of LPD, the Inducter class is a UDP socket listening on a specific multicast group'''
    def __init__(self, host_peer, mcast):
        '''Initialize with the Unique ID of host and Multicast group'''
        self.host=host_peer
        (self.mcast_addr,self.mcast_port)=mcast
        self.peer_list=set([])
        self.handler=MessageHandler(self)

    def startProtocol(self):
        self.transport.setTTL(32)
        #Join the multicast address, so we can receive replies:
        print type(self.transport)
        self.transport.joinGroup(self.mcast_addr)
        self.transport.setLoopbackMode(1)
        self.react=self.transport.reactor
        #Register UNHOOK trigger on disconnect
        self.react.addSystemEventTrigger('before', 'shutdown', self._disconnect)
        self.broadcast_hook(2)

    def _disconnect(self):
        print 'disconnecting'
        message=Message(2,[self.host.uid])
        self.transport.write(str(message), (self.mcast_addr, self.mcast_port))
    
    def broadcast_hook(self, this_call):
        '''Broadcasts a FISH_HOOK on Multicast group'''
        print 'brodcasting hook'
        peer_uid=map(lambda x:x.uid, self.peer_list)
        peer_uid.insert(0,self.host.uid)
        message=Message(1,peer_uid)
        print repr(message)
        self.transport.write(str(message), (self.mcast_addr, self.mcast_port))
        next_call=this_call
        if this_call < 256:
            next_call*=2
        self.react.callLater(next_call, self.broadcast_hook, next_call)
        
    def assert_existance(self):
        print 'asserting self'
        message=Message(3,[self.host.uid])
        self.transport.write(str(message), (self.mcast_addr, self.mcast_port))
    
    def datagramReceived(self, message_str, addr):
        print message_str,addr
        if addr == self.host.ip:
            return
        message=Message(message_str)
        self.handler.handle(message, addr)
        

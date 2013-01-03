from twisted.internet.protocol import DatagramProtocol
from twisted.internet import reactor
import logging

class Inducter(DatagramProtocol):
    '''The heart of LPD, the Inducter class is a UDP socket 
        listening on a specific multicast group'''
    def __init__(self, mcast):
        '''Initialize with the Unique ID of host and Multicast group'''
        self.mcast_addr=mcast
        self.callingFunction=None

    def broadcast(self,message):
        '''Broadcast given message on the multicast address'''
        logging.debug('Broadcasting message {0}'.format(repr(message)))
        self.transport.write(str(message),self.mcast_addr)

    def startProtocol(self):
        self.transport.setTTL(32)
        #Join the multicast address, so we can receive replies:
        self.transport.joinGroup(self.mcast_addr[0])
        logging.info('Multicast listening at {0}'.format(str(self.mcast_addr)))
        self.transport.setLoopbackMode(0)
        
    def addHandler(self, handleFn):
        '''Add a function to handle incoming multicast messages'''
        if not callable(handleFn):
            raise MulticastError(1,'Supplied handler is not callable')
        self.callingFunction=handleFn

    def datagramReceived(self, datagram, addr):
        if not self.callingFunction is None:
            self.callingFunction(datagram, addr)

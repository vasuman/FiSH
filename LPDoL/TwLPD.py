from twisted.internet.protocol import DatagramProtocol
from twisted.internet import reactor
import socket as sck
from pickle import dumps,loads
from collections import namedtuple, Counter

class Inducter(DatagramProtocol):
    '''The heart of LPD, the Inducter class is a UDP socket listening on a specific multicast group'''
    def __init__(self, uid, mcast):
        '''Initialize with the Unique ID of host and Multicast group'''
        self.uid=uid
        (self.mcast_addr,self.mcast_port)=mcast
        self.peer_list=None

    def startProtocol(self):
        self.transport.setTTL(32)
        #Join the multicast address, so we can receive replies:
            self.transport.joinGroup(self.mcast_addr)
        self.transport.setLoopbackMode(1)
        #Register UNHOOK trigger on disconnect
        self.transport.reactor.addSystemEventTrigger('before', 'shutdown', self._disconnect)

    def _disconnect(self):
        message='FISH_UNHOOK:{0}'.format(self.uid)
        self.transport.write(message, (self.mcast_addr, self.mcast_port))
    
    def broadcast(self):
        '''Broadcasts a FISH_HOOK on Multicast group'''
        message='FISH_HOOK:{0}'.format(self.uid)
        self.transport.write(message, (self.mcast_addr, self.mcast_port))

    def _induct(self, data, addr):
        extract_index=lambda x:x.index
        # Check if self in not yet inducted
        if self.peer_list is None:
            return
        max_index=max(self.peer_list, key=extract_index).index
        new_peer=Peer(uid=data, addr=addr, index=max_index+1)
        self.peer_list.add(new_peer)
        # Increment no. initialization requests 
        self._init_reqs[data]+=1
        data_str=pickle.dumps(self.peer_list)
        message='FISH_PL:{0}'.format(data_str)
        self.transport.write(message, (self.mcast_addr, self.mcast_port))

    def _inducted(self, data, addr):
        del self._init_reqs[data]
    
    def _list_m(self, data, addr):
        try:
            peer_list=pickle.loads(data)
            # Check for malicious code
            if not type(peer_list) is set:
                raise MessageException(3,'Invalid pickled object')
        except:
            raise MessageException(4,'Invalid pickling string')
        if self.peer_list is None:
            self.peer_list=peer_list
            # Host in now inducted
            msg='FISH_HOOKED:{0}'.format(self.uid)
            self.transport.write(msg,(self.mcast_addr,self.mcast_port))
        # Check for confilcting peer lists
        elif self.peer_list != peer_list:
            self._conflict(peer_list, addr)
    
    def _conflict(self, x_p_list, addr):
        pass

    def _remove(self, data, addr):
        del self.peer_list[data]
        

    def datagramReceived(self, message, addr):
        print message,addr
        

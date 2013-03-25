from common import *
from twisted.internet import reactor
import logging


def repr_peer(peer_obj):
    return (peer_obj.uid, peer_obj.name)

class MessageHandler(object):
    def __init__(self, host_peer, ofstream, peer_list):
        self.op_func=ofstream
        self.host=host_peer
        self.peer_list=peer_list
        self.enabled=True
        self.hook_gap=1
        self.hook_ID=None
        #Mapping message keys to handling functions
        self.FUNC_CODES={
            1:self._respond_hook,
            2:self._del_peer,
            3:self._add_peer}
        #Add HOOK trigger
        reactor.addSystemEventTrigger('after', 'startup', self.hook)
        if reactor.running:
            self.hook()
        #Add UNHOOK trigger
        reactor.addSystemEventTrigger('before', 'shutdown', self.unhook)

    def _respond_hook(self,source_peer,message):         
        self.peer_list.add(source_peer)
        if not self.host.uid in map(lambda x:x[0], message.data):
            self.live()
            
    def _add_peer(self,source_peer,message):
        self.peer_list.add(source_peer)
    
    def _del_peer(self,source_peer,message):
        self.peer_list.discard(source_peer)

    def handle(self,data,ip):
        '''A sink that accepts incoming Peer Discovery data'''
        if not self.enabled:
            return -2
        try:
            message=PDMessage(message_str=data)
        except MessageException as e:
            return -1
        source_uid, source_name=message.data[0]
        if source_uid == self.host.uid:
            logging.debug('Loopback. Ehh!')
            return -3
        logging.debug('Recieved {0} from {1}'.format(repr(message), ip))
        source_peer=Peer(uid=source_uid, name=source_name, addr=ip[0])
        self.FUNC_CODES[message.key](source_peer, message)
        
    def hook(self):
        '''Broadcasts a LPDOL_HOOK on Multicast group with exponential time delays'''
        if not self.enabled:
            return
        #Generate list of peer UIDs
        peer_uid=map(repr_peer, self.peer_list.items)
        #Prefix host UID to list
        peer_uid.insert(0,repr_peer(self.host))
        try:
            message=PDMessage(1,peer_uid)
        except:
            logging.error('Peer Container has been corrupted')
            self.peer_list.items=[]
            return
        logging.debug('Hooking..')
        self.write(message)
        #Generate next time gap -- Exponential back-off
        if self.hook_gap < 256: self.hook_gap*=2
        #Register trigger with reactor
        self.hook_ID=reactor.callLater(self.hook_gap, self.hook)

    def live(self):
        '''Asserts existance by broadcasting LPDOL_LIVE'''
        message=PDMessage(3,[repr_peer(self.host)])
        logging.debug('Asserting life.')
        self.write(message)

    def unhook(self):
        '''Broadcasts a LPDOL_UNHOOK message before disconnecting'''
        if not self.enabled:
            return
        message=PDMessage(2,[repr_peer(self.host)])
        logging.debug('Unhooking from swarm.')
        self.write(message)

    def setOutputStream(self, fn):
        self.op_func=fn

    def write(self, message):
        if not self.enabled:
            return
        try:
            self.op_func(message)
        except Exception as e:
            logging.error('Unable to write messages: '+str(e))

    def resetAll(self):
        self.hook_gap=1
        # self.peer_list.items=[]
        self.enabled=True
        try:
            self.hook_ID.cancel()
        except:
            pass
        self.hook()

from common import *
from twisted.internet import reactor

class MessageHandler(object):
    def __init__(self, host_peer, ofstream):
        self.op_func=ofstream
        self.host=host_peer
        self.peer_list=set([])
        #Mapping message keys to handling functions
        self.FUNC_CODES={
                1:self._respond_hook,
                2:self._del_peer,
                3:self._add_peer}
        #Add HOOK trigger
        reactor.addSystemEventTrigger('after', 'startup', self.hook, 1)
        #Add UNHOOK trigger
        reactor.addSystemEventTrigger('before', 'shutdown', self.unhook)

    def _respond_hook(self,source_peer,message):
        self.peer_list.add(source_peer)
        if not self.host.uid in message.data:
            self.live()

    def _add_peer(self,source_peer,message):
        self.peer_list.add(source_peer)
    
    def _del_peer(self,source_peer,message):
        self.peer_list.discard(source_peer)

    #Changes need to be made to LMessage befor we can register custom handlers
    #--validation of UIDs
    # def registerCustomHandler(self, message_key, handlingFn):
    #     if not callable(handlingFn):
    #         return -2
    #     if message_key in self.FUNC_CODES:
    #         return -1
    #     self.FUNC_CODES[message_key]=handlingFn

    def handle(self,data,ip):
        try:
            message=LMessage(message_str=data)
        except MessageException as e:
            return
        source_peer=Peer(message.data[0], ip)
        self.FUNC_CODES[message.key](source_peer, message)
        
    def hook(self, this_call):
        '''Broadcasts a FISH_HOOK on Multicast group'''
        #Generate list of peer UIDs
        peer_uid=map(lambda x:x.uid, self.peer_list)
        #Prefix host UID to list
        peer_uid.insert(0,self.host.uid)
        message=LMessage(1,peer_uid)
        self.op_func(message)
        #Generate next time gap -- Exponential back-off
        next_call=this_call
        if this_call < 256: next_call*=2
        #Register trigger with reactor
        reactor.callLater(next_call, self.hook, next_call)
        
    def live(self):
        '''Asserts existance by broadcasting FISH_LIVE'''
        message=LMessage(3,[self.host.uid])
        self.op_func(message)

    def unhook(self):
        '''Broadcasts a FISH_UNHOOK message before disconnecting'''
        message=LMessage(2,[self.host.uid])
        self.op_func(message)

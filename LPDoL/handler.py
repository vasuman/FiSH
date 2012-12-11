from common import Peer, LMessage
from twisted.internet import reactor

class MessageHandler(object):
    def __init__(self, host_peer, ofstream):
        #Assigning shorthand for quick calls
        self.op_func=ofstream
        self.host=host_peer
        self.peer_list=set([])
        self.FUNC_CODES={
                1:self._respond_hook,
                2:self._del_peer,
                3:self._add_peer}
        reactor.addSystemEventTrigger('before', 'shutdown', self.disconnect)
        self.hook(2)

    def _respond_hook(self,message,ip):
        new_peer=Peer(message.data[0], ip)
        self.peer_list.add(new_peer)
        if not self.mc_sock.host_peer.uid in message.data:
            self.live()

    def _add_peer(self,message,ip):
        new_peer=Peer(message.data[0], ip)
        self.peer_list.add(new_peer)
    
    def _del_peer(self,message,ip):
        new_peer=Peer(message.data[0], ip)
        self.peer_list.discard(new_peer)

    def handle(self,message,ip):
        self.FUNC_CODES[message.key](message,ip)
        
    def hook(self, this_call):
        '''Broadcasts a FISH_HOOK on Multicast group'''
        peer_uid=map(lambda x:x.uid, self.peer_list)
        peer_uid.insert(0,self.host.uid)
        message=LMessage(1,peer_uid)
        print repr(message)
        self.op_func(message)
        next_call=this_call
        if this_call < 256: next_call*=2
        reactor.callLater(next_call, self.hook, next_call)
        
    def live(self):
        print 'asserting self'
        message=LMessage(3,[self.host.uid])
        self.op_func(message)

    def disconnect(self):
        message=LMessage(2,[self.host.uid])
        self.op_func(message)

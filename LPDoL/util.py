from common import Peer
class MessageHandler(object):
    def __init__(self, mc_sock):
        self.mc_sock=mc_sock
        self.FUNC_CODES={
                1:self.respond_hook,
                2:self.del_peer,
                3:self.add_peer}

    def respond_hook(self,message,ip):
        new_peer=Peer(message.data[0], ip)
        self.mc_sock.peer_list.add(new_peer)
        if not self.mc_sock.uid in message.data:
            self.mc_sock.assert_existance()

    def add_peer(self,message,ip):
        new_peer=Peer(message.data[0], ip)
        self.mc_sock.peer_list.add(new_peer)
    
    def del_peer(self,message,ip):
        new_peer=Peer(message.data[0], ip)
        self.mc_sock.peer_list.discard(new_peer)

    def handle(self,message,ip):
        self.FUNC_CODES[message.key](message,ip)



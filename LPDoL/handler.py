from common import *
from twisted.internet import reactor

MSG_CODES={
        1:'LPDOL_HOOK',
        2:'LPDOL_UNHOOK',
        3:'LPDOL_LIVE',
        4:'LPDOL_NAMETAKEN'}

KEY_MUL_MEM=[1]

VALID_FN={
    1:validate_identity,
    2:validate_identity,
    3:validate_identity,
    4:validate_identity,
}

class LMessage(object):
    '''All communication between peers is done by objects of this class'''
    def __init__(self,key=None,data=None,message_str=None):
        '''Creates a message object from key and data
        key -- int : refer MSG_CODES variable
        data -- list of data members
        If a message_str is passed other values are neglected
        Creates a message object from string of form 
            <key>:<data>'''
        if not message_str is None:
            key,data=self._parse_message(message_str)
        #Standard validation of key and data
        assert type(key) == int, 'Invalid key type'
        assert type(data) == list, 'Invalid data'
        self._validate_message(key,data)
        self.key=key
        self.data=data
        #DEBUG STATEMENT!!!!!
        print repr(self)
    
    def __repr__(self):
        '''Human understandable representation of message'''
        return MSG_CODES[self.key]+':'+';'.join(['.'.join(it) for it in self.data])

    def __str__(self):
        '''Returns a serialized representation of object of form
            <key>:<data>'''
        return str(self.key)+':'+';'.join(['.'.join(it) for it in self.data])
                
    def _validate_message(self,key,data):
        #Checking if <key> is valid index
        if not key in MSG_CODES.keys():
            raise MessageException(4,'Invalid key index')
        validation_function=VALID_FN[key]
        #Checking all data items
        map(validation_function,data)
        #Checking for underflow
        if len(data) == 0:
            raise MessageException(8,'Too few arguments')
        #Only certain message is supposed to have multiple data members
        if (not key in KEY_MUL_MEM) and len(data) != 1:
                raise MessageException(7,'Too many members')

    def _parse_message(self,message):
        #Checking for class seperator
        if not ':' in message:
            raise MessageException(1,'Malformed message string')
        chop_msg=message.split(':')
        #Checking if type '<key>:<message>'
        if not len(chop_msg) == 2:
            raise MessageException(2,'Invalid message parameters')
        #Checking if type(<key>) is int
        try:
            key=int(chop_msg[0])
        except:
            raise MessageException(3,'Invalid key type')
        data_str=chop_msg[1]
        data=data_str.split(';')
        data=[tuple(it.split('.')) for it in data]
        return (key,data)

class MessageHandler(object):
    def __init__(self, host_peer, ofstream):
        self.op_func=ofstream
        self.host=host_peer
        self.peer_list=set([])
        self.hook_gap=1
        #Mapping message keys to handling functions
        self.FUNC_CODES={
                1:self._respond_hook,
                2:self._del_peer,
                3:self._add_peer,
                4:self._name_taken}
        #Add HOOK trigger
        reactor.addSystemEventTrigger('after', 'startup', self.hook)
        #Add UNHOOK trigger
        reactor.addSystemEventTrigger('before', 'shutdown', self.unhook)

    def _respond_hook(self,source_peer,message):
        if source_peer.name in [x.name for x in peer_list]:
            if source_peer.name != 'anon':
                self.naming_conflict(source_peer)
                return             
        self.peer_list.add(source_peer)
        if not self.host.uid in message.data:
            self.live()

    def _name_taken(self,source_peer,message):
        raise PeerDiscoveryError(1,'Name is already taken')
            
    def _add_peer(self,source_peer,message):
        self.peer_list.add(source_peer)
    
    def _del_peer(self,source_peer,message):
        self.peer_list.discard(source_peer)

    def handle(self,data,ip):
        try:
            message=LMessage(message_str=data)
        except MessageException as e:
            print e
            return
        source_uid, source_name=message.data[0]
        source_peer=Peer(uid=source_uid, name=source_name, addr=ip)
        self.FUNC_CODES[message.key](source_peer, message)
        
    def hook(self):
        '''Broadcasts a LPDOL_HOOK on Multicast group'''
        #Generate list of peer UIDs
        peer_uid=map(lambda x:(x.uid, x.name), self.peer_list)
        #Prefix host UID to list
        peer_uid.insert(0,(self.host.uid, self.host.name))
        message=LMessage(1,peer_uid)
        self.op_func(message)
        #Generate next time gap -- Exponential back-off
        if self.hook_gap < 256: self.hook_gap*=2
        #Register trigger with reactor
        reactor.callLater(self.hook_gap, self.hook)
    
    def naming_conflict(self,source_peer):
        '''Alerts a peer that the name is already in use'''
        message=LMessage(4,[(source_peer.uid, source_peer.name)])
        self.op_func(message)

    def live(self):
        '''Asserts existance by broadcasting LPDOL_LIVE'''
        message=LMessage(3,[(self.host.uid, self.host.name)])
        self.op_func(message)

    def unhook(self):
        '''Broadcasts a LPDOL_UNHOOK message before disconnecting'''
        message=LMessage(2,[(self.host.uid, self.host.name)])
        self.op_func(message)

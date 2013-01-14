from collections import namedtuple
from twisted.internet import reactor
from util.message import *

#Defining all message validation functions below

INVALID_CHARS=[';',':','\\','/',' ','\'','\"',',']

def validate_uid(uid):
    #Check for 32 byte string
    if not len(uid) == 32:
        return False
    #Check if valid hexadecimal number
    try:
        int(uid,16)
    except:
        return False
    return True

def validate_name(name_str):
    assert type(name_str)==str, 'Name must be a string'
    #Must not exceed maximum length
    if len(name_str)>25:
        return False
    #Must not contain invalid characters
    for ch in INVALID_CHARS:
        if ch in name_str:
            return False
    return True

def validate_identity(id_tuple):
    if len(id_tuple) != 2:
        return False
    uid,name=id_tuple
    return validate_name(name) and validate_uid(uid)

#Defining a message context below

MSG_CODES_VALID={
        1:('HOOK',validate_identity),
        2:('UNHOOK',validate_identity),
        3:('LIVE',validate_identity)}

KEY_MUL_MEM=[1]


LPDoL_context=MessageContext(family='LPDOL', message_codes=MSG_CODES_VALID, key_multiple=KEY_MUL_MEM)


class PDMessage(LMessage):
    '''Special module designed to transmit dynDNS messages on multicast 
    -- initiates all messages with LPDoL context'''
    def __init__(self, *args, **kwargs):
        self.context=LPDoL_context
        super(PDMessage, self).__init__(*args, **kwargs)

Peer=namedtuple('Peer','uid addr name')

class PeerContainer(list):
    def __init__(self, onAdd, onDel):
        super(PeerContainer, self).__init__()
        self.aT=onAdd
        self.dT=onDel

    def add(self, peer_obj):
        flag=True
        for item in self:
            if item.addr == peer_obj.addr:
                self.remove(item)
                flag=False
        self.append(peer_obj)
        if flag:
            reactor.callInThread(self.aT, self)

    def discard(self, peer_obj):    
        for item in self:
            if item.addr == peer_obj.addr:
                self.remove(item)
                reactor.callInThread(self.dT, self)

class LPDoLError(Exception):
    '''Base Error class -- all other exceptions inherit from this'''
    def __init__(self, err, message):
        self.err=err
        self.message=message

class PeerDiscoveryError(LPDoLError):
    '''Instantiated when errors thrown by handler'''
    def __str__(self):
        return 'Peer Discovery Failure - [ERROR {0.err}]: {0.message}'.format(self)

class MulticastError(LPDoLError):
    def __str__(self):
        return 'Socket Error - [ERROR {0.err}]: {0.message}'.format(self)

from collections import namedtuple

Peer=namedtuple('Peer','uid addr index')

MSG_CODES={
        1:'FISH_HOOK',
        2:'FISH_UNHOOK',
        3:'FISH_LIVE',
        4:'FISH_DEAD'}

KEY_MUL_UID=[1]

class LPDoLError(Exception):
    '''Base Error class -- all other exceptions inherit from this'''
    def __init__(self, err, message):
        self.err=err
        self.message=message

class MessageException(LPDoLError):
    '''Prevents mutated or malicious messages'''
    def __str__(self):
        return 'Invalid message - [ERROR {0.err}]: {0.message}'.format(self)

class PeerDiscoveryError(LPDoLError):
    def __str__(self):
        return 'Peer Discovery Failure - [ERROR {0.err}]: {0.message}'.format(self)

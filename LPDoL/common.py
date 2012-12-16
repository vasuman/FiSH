from collections import namedtuple

Peer=namedtuple('Peer','uid addr name')


INVALID_CHARS=[';',':','\\','/',' ','\'','\"',',']


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

class MulticastError(LPDoLError):
    def __str__(self):
        return 'Socket Error - [ERROR {0.err}]: {0.message}'.format(self)

def validate_uid(uid):
    #Check for 32 byte string
    if not len(uid) == 32:
        raise MessageException(5,'Invalid UID length')
    #Check if valid hexadecimal number
    try:
        int(uid,16)
    except:
        raise MessageException(6,'UID not hexadecimal')
    return uid


def validate_name(name_str):
    assert type(name_str)==str, 'Name must be a string'
    #Must not exceed maximum length
    if len(name_str)>25:
        raise MessageException(10,'Name is too long')
    #Must not contain invalid characters
    for ch in INVALID_CHARS:
        if ch in name_str:
            raise MessageException(11,'Name contains invalid characters')

def validate_identity(id_tuple):
    if len(id_tuple) != 2:
        raise MessageException(9, 'Invalid number of ID parameters')
    uid,name=id_tuple
    validate_name(name)
    validate_uid(uid)


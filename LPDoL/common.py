from collections import namedtuple
import util.message as m

Peer=namedtuple('Peer','uid addr name')

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

m.MSG_CODES_VALID={
        1:('LPDOL_HOOK',validate_identity),
        2:('LPDOL_UNHOOK',validate_identity),
        3:('LPDOL_LIVE',validate_identity),
        4:('LPDOL_NAMETAKEN',validate_identity)}

m.KEY_MUL_MEM=[1]

class LPDoLError(Exception):
    '''Base Error class -- all other exceptions inherit from this'''
    def __init__(self, err, message):
        self.err=err
        self.message=message

class PeerDiscoveryError(LPDoLError):
    def __str__(self):
        return 'Peer Discovery Failure - [ERROR {0.err}]: {0.message}'.format(self)

class MulticastError(LPDoLError):
    def __str__(self):
        return 'Socket Error - [ERROR {0.err}]: {0.message}'.format(self)




#common.py
import util.message

def is_error(error_tup):
    if not len(error_tup) == 2:
        return False
    try:
        code, msg=error_tup
        code=int(code)
        assert type(msg)==str
    except:
        return False
    return True

def verify_sha1(sha):
    #Check for 40 byte string
    if not len(sha) == 40:
        return False
    #Check if valid hexadecimal number
    try:
        int(sha,16)
    except:
        return False
    return True

# Message codes from 1-3 are sent from client to server, 
# error messages - code 4; is only sent from server to client 
util.message.MSG_CODES_VALID={
        1:('LIST_HASH_TABLE',),
        2:('LOAD_FILE',verify_sha1),
        3:('START_TRANSFER',),
        4:('ERROR',is_error)}

util.message.NO_PARAM=[1,3]

from util.message import *


class FTError(Exception):
    '''Base Error class -- all other exceptions inherit from this'''
    def __init__(self, err, message):
        self.err=err
        self.message=message

    def __str__(self):
        return '{0.err}.{0.message}'.format(self)

class IndexerException(FTError):
    '''Is raised when an error occurs while accessing requested file'''
    def __repr__(self):
        return 'FILE_EXCEPTION - [ERROR {0.err}]: {0.message}'.format(self)

class DaemonException(FTError):
    '''Is raised when an invalid FiTd call occurs'''
    def __repr__(self):
        return 'FITD_XCP - [ERROR {0.err}]: {0.message}'.format(self)

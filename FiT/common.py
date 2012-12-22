#common.py
import util.message as m

def is_error(error_str):
    if not '.' in error_str:
        return False
    try:
        code, msg=error_str.split('.')
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

m.MSG_CODES_VALID={
        1:('LIST_HASH_TABLE',lambda x:x == 1),
        2:('LOAD_FILE',verify_sha1),
        3:('START_TRANSFER',lambda x:x == 3),
        4:('ERROR',is_error)}

m.KEY_MUL_MEM=[]

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



#common.py
from util.message import *

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

def verify_sha1(sh_tup):
    sha=sh_tup[0]
    #Check for 40 byte string
    if not len(sha) == 40:
        return False
    #Check if valid hexadecimal number
    try:
        int(sha,16)
    except:
        return False
    return True

def is_num(data):
    try:
        int(data[0])
    except:
        return False
    return True

# Message codes from 1-2 are sent from client to server, 
# error messages - code 4; is only sent from server to client 
MSG_CODES_VALID={
        1:('LIST_HASH_TABLE',),
        2:('LOAD_FILE',verify_sha1),
        3:('START_TRANSFER',is_num),
        4:('ERROR',is_error)}

NO_PARAM=[1]

FIT_context=MessageContext(family='FIT', message_codes=MSG_CODES_VALID, no_arg=NO_PARAM)

class FiTMessage(LMessage):
    def __init__(self, *args, **kwargs):
        self.context=FIT_context
        super(FiTMessage, self).__init__(*args, **kwargs)
        
from twisted.internet.protocol import Protocol

class StreamLineProtocol(Protocol):
    """StreamLineProtocol buffers all input data till newline character is recieved
    which denotes completion of one message this message is then passed onto 
    the serviceMessage function which MUST be overridden"""
    def __init__(self):
        self.buffLine = ''
        self.spHandler = None

    def connectionLost(self, reason):
        pass

    def sendLine(self, line):
        self.transport.write(str(line)+'\n')

    def escape_newline(self, line):
        return line.replace('\n','').replace('\r','')

    def registerSpHandler(self, pFn):
        self.spHandler=pFn

    def unregisterSpHandler(self):
        self.spHandler = None

    def dataReceived(self, buff_str):
        if self.spHandler:
            self.spHandler(buff_str)
            return
        for char in buff_str:
            self.buffLine+=char
            if char == '\n':
                request_str=self.escape_newline(self.buffLine)
                self.serviceMessage(request_str)
                self.buffLine=''

    def serviceMessage(self, message):
        pass
        

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

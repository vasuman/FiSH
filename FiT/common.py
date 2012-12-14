#common.py

INVALID_CHARS=[';',':','\\','/',' ','\'','\"',',']

class FTError(Exception):
    '''Base Error class -- all other exceptions inherit from this'''
    def __init__(self, err, message):
        self.err=err
        self.message=message

class IndexerException(FTError):
    '''Is raised when an error occurs while accessing requested file'''
    def __str__(self):
        return 'FILE_EXCEPTION - [ERROR {0.err}]: {0.message}'.format(self)

class IdentException(FTError):
    '''Is raised when invalid credentials supplied'''
    def __str__(self):
        return 'INVALID_IDENTITY - [ERROR {0.err}]: {0.message}'.format(self)

def validate_uid(uid):
    assert type(uid)==str, 'UID must be a string'
    #Check for 32 byte string
    if not len(uid) == 32:
        raise IdentException(1,'Invalid UID length')
    #Check if valid hexadecimal number
    try:
        int(uid,16)
    except:
        raise IdentException(2,'UID not hexadecimal')

def validate_name(name_str):
    assert type(name_str)==str, 'Name must be a string'
    if len(name_str)>25:
        raise IdentException(4,'Name is too long')
    for ch in INVALID_CHARS:
        if ch in name_str:
            raise IdentException(3,'Name contains invalid characters')
    # contains=reduce((lambda x,y: x or y), [ch in name_str for ch in INVALID_CHARS], False)



class IdentString(object):
    def __init__(self, name=None, uid=None, ip=None, data_str=None): 
        if not data_str is None:
            data=self._parse_message(data_str)
            uid, ip, name=data
        validate_name(name)
        validate_uid(uid)
        assert type(ip)==str, 'Must enter valid IP address'
        self.name = name
        self.uid = uid
        self.ip = ip

    def _parse_message(self, data_str):
        if not ':' in data_str:
            raise IdentException(5,'Delimiter not present')
        data=data_str.split(':')
        if len(data) != 3:
            raise IdentException(6,'Invlaid no. of fields')
        return data

    def __str__(self):
        return '{0.uid}:{0.ip}:{0.name}'.format(self)

    


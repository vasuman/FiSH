from common import MSG_CODES, KEY_MUL_UID, MessageException

class Message(object):
    '''All communication between peers is done by objects of this class'''
    def __init__(self,message):
        '''Creates a message object from string of form 
            <key>:<data>'''
        self.key,self.data=self._parse_message(message)

    def __init__(self,key,data):
        '''Creates a message object from key and data
        key -- int : refer MSG_CODES variable
        data -- list of (16 byte hexadecimal UIDs)'''
        #Standard validation of key and data
        assert type(key) == int, 'Invalid key type'
        assert type(data) == list, 'Invalid data'
        self._validate_message(key,data)
        self.key=key
        self.data=data
    
    def __repr__(self):
        '''Human understandable representation of message'''
        return MSG_CODES[self.key]+':'+';'.join(self.data)

    def __str__(self):
        '''Returns a serialized representation of object of form
            <key>:<data>'''
        return str(self.key)+':'+';'.join(self.data)
                
    def _validate_uid(self,uid):
        #Check for 32 byte string
        if not len(uid) == 32:
            raise MessageException(5,'Invalid UID length')
        #Check if valid hexadecimal number
        try:
            int(uid,16)
        except:
            raise MessageException(6,'UID not hexadecimal')
        return uid
    
    def _validate_message(self,key,data):
        #Checking if <key> is valid index
        if not key in MSG_CODES.keys():
            raise MessageException(4,'Invalid key index')
        #Checking all UIDs
        map(self._validate_uid,data)
        #Checking for underflow
        if len(data) == 0:
            raise MessageException(8,'Too few arguments')
        #Only certain message is supposed to have multiple UIDs
        if (not key in KEY_MUL_UID) and len(data) != 1:
                raise MessageException(7,'Too many UIDs')

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
        #Validate the <message> parameter
        self._validate_message(key,data)
        return (key,data)


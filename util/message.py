class MessageException(Exception):
    '''Prevents mutated or malicious messages'''
    def __init__(self, err, message):
        self.err=err
        self.message=message

    def __str__(self):
        return 'Invalid message - [ERROR {0.err}]: {0.message}'.format(self)

#The following valiables MUST be overwritten while importing to define message members

#The MSG_CODES_VALID variable stores the names and validation functions 
#for the corresponding keys in the form of a two member tuple
MSG_CODES_VALID={}

#The KEY_MUL_MEM variable is used to allow certain keys to hold multiple data
KEY_MUL_MEM=[]

class LMessage(object):
    '''All communication between peers is done by objects of this class'''
    def __init__(self,key=None,data=None,message_str=None):
        '''Creates a message object from key and data
        key -- int : refer MSG_CODES_VALID variable
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
        return MSG_CODES_VALID[self.key][0]+':'+';'.join(['.'.join(it) for it in self.data])

    def __str__(self):
        '''Returns a serialized representation of object of form
            <key>:<data>'''
        return str(self.key)+':'+';'.join(['.'.join(it) for it in self.data])
                
    def _validate_message(self,key,data):
        #Checking if <key> is valid index
        if not key in MSG_CODES_VALID.keys():
            raise MessageException(4,'Invalid key index')
        validation_function=MSG_CODES_VALID[key][1]
        #Checking all data items
        for valid in map(validation_function,data):
        	if not valid:
        		raise MessageException(7, 'Invalid data member')
        #Checking for underflow
        if len(data) == 0:
            raise MessageException(5,'Too few arguments')
        #Only certain message is supposed to have multiple data members
        if (not key in KEY_MUL_MEM) and len(data) != 1:
                raise MessageException(6,'Too many members')

    def _parse_message(self,message):
        #Checking for class seperator
        if not ':' in message:
            raise MessageException(1,'Malformed message string')
        chop_msg=message.split(':')
        #Checking if type '<key>:<data>'
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
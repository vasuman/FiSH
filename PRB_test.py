from twisted.internet import reactor
from FiT.probe import *


def fHTFn(success, fHT):
    if success:
        fileHash=pPrint(fHT)
        f=open('temp_file','wb')
        reactor.connectTCP(ip, 17395, FTFactory(fileHash, f, doneCb))
    else:
        print 'Failed to get HT'

def pPrint(fHT):
    assoc_list={}
    for i,(k,v) in enumerate(fHT.iteritems()):
        assoc_list[i]=k
        print i,':',' - '.join(map(str,v))
    num=int(raw_input('Enter file index: '))
    return assoc_list[num]

def doneCb(success):
    print 'File Transfer done: ', success
    reactor.stop()

if __name__ == '__main__':
    ip=raw_input('Enter IP: ')
    reactor.connectTCP(ip, 17395, FHFactory(fHTFn))
    reactor.run()


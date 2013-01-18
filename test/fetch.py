# from twisted.internet import glib2reactor
# glib2reactor.install()
import os
from twisted.internet import reactor
from FiT.probe import *
import sys
from twisted.internet.defer import Deferred

def fHTFn(fHT):
    fileHash=pPrint(fHT)
    f=open(fHT[fileHash][0],'wb')
    d=Deferred()
    d.addCallback(doneCb)
    d.addErrback(failed)
    reactor.connectTCP(ip, 17395, FTFactory(fileHash, f, d))

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

def failed(reason):
    print 'Failed: ',reason
    reactor.stop()

if __name__ == '__main__':
    ip=sys.argv[1]
    d=Deferred()
    d.addCallback(fHTFn)
    d.addErrback(failed)
    reactor.connectTCP(ip, 17395, FHFactory(d))
    reactor.run()


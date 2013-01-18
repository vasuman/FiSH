from FiT.indexer import *
from FiT.daemon import *
from twisted.internet import reactor
from twisted.internet.defer import Deferred
from twisted.internet.threads import deferToThread
from FiT.probe import *
import sys
from LPDoL.multicast import Inducter
from LPDoL.handler import MessageHandler
from LPDoL.common import *
from uuid import uuid1
import logging

run_string='''Use the following commands:-
list - list the global file index
refresh - refresh the local file index
exit - self explanatory!'''

addr_files={}
inxr=None

def bindfHT(addr, fHT):
    addr_files[addr]=fHT

def getFile(addr, fHash, name):
    global inxr
    f=inxr.saveFile(name)
    d=Deferred()
    d.addCallback(doneCb)
    d.addErrback(failed)
    reactor.connectTCP(addr, 17395, FTFactory(fHash, f, d))

def doneCb(success):
    inform('Succesfull file transfer')

def getFileHT(addr):
    fHTFn=lambda x: bindfHT(addr, x)
    d=Deferred()
    d.addCallback(fHTFn)
    d.addErrback(failed)
    reactor.connectTCP(addr, 17395, FHFactory(d))

def failed(reason):
    print reason

def refAdd(peer_list):
    addr_list=map(lambda x:x.addr, peer_list)
    for addr in addr_list:
        if not addr in addr_files:
            inform('Exploring peer at {0}'.format(addr))
            try:
                getFileHT(addr)
            except Exception as e:
                print 'Failed to retrieve from address due to {0}'.format(e)

def inform(info):
    print '\n'+info+'>>'

def refDel(peer_list):
    addr_list=map(lambda x:x.addr, peer_list)
    for addr in addr_files.keys():
        if not addr in addr_list:
            del addr_files[addr]

def startFTD():
    global inxr
    path=sys.argv[1]
    inxr=FileIndexer(path)
    reactor.listenTCP(17395, IFFactory(inxr))

def startPD():
    p=Peer(uid=uuid1().hex, name='anon',addr='127.0.0.1')
    p_l=PeerContainer(refAdd, refDel)
    i=Inducter(('224.0.2.38',8999))
    reactor.listenMulticast(8999,i)
    h=MessageHandler(p, i.broadcast, p_l)
    i.addHandler(h.handle)

def prompt():
    while 1:
        q=raw_input('>>')
        if q == 'exit': 
            reactor.stop()
            print 'Exiting.....'
            break
        elif q == 'list':
            handleFT()
        elif q == 'refresh':
            inxr._generate_index()
            print 'Local file index refreshed'
            
def handleFT():
    assoc_list={}
    it=0
    for addr in addr_files.keys():
        fHT=addr_files[addr]
        for (k,v) in fHT.iteritems():
            assoc_list[it]=addr,k
            print it,':',' - '.join(map(str,v))
            it+=1
    if assoc_list != {}:
        num=int(raw_input('Enter file index [-1 to cancel]: '))
        if num == -1: return
        addr,fHash=assoc_list[num]
        getFile(addr, fHash, addr_files[addr][fHash][0])
    else:
        print 'No files available'

def main():
    logging.basicConfig(level=logging.INFO)
    startFTD()
    startPD()
    print run_string
    deferToThread(prompt)
    reactor.run()

if __name__ == '__main__':
    main()

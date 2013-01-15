#!/usr/bin/env python2

from LPDoL.multicast import Inducter
from LPDoL.handler import MessageHandler
from LPDoL.common import *
from uuid import uuid1
from twisted.internet import reactor

def cb(x):
	print x
	
if __name__ == '__main__':
	p=Peer(uid=uuid1().hex, name='anon',addr='127.0.0.1')
	p_l=PeerContainer(cb, cb)
	i=Inducter(('224.0.2.38',8999))
	reactor.listenMulticast(8999,i)
	h=MessageHandler(p, i.broadcast, p_l)
	i.addHandler(h.handle)
	reactor.run()

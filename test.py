#!/usr/bin/env python2
from LPDoL.multicast import Inducter
from LPDoL.handler import MessageHandler
from LPDoL.common import Peer
from uuid import uuid1
from twisted.internet import reactor

p=Peer(uid=uuid1().hex,name='anon',addr='127.0.0.1')
i=Inducter(('224.0.2.38',8999))
h=MessageHandler(p, i.broadcast)
i.addHandler(h.handle)
reactor.listenMulticast(8999,i)
reactor.run()
#!/usr/bin/env python2
from LPDoL.multicast import Inducter
from LPDoL.handler import MessageHandler
from LPDoL.common import Peer
from uuid import uuid1
# import netifaces
from twisted.internet import reactor

# def get_ip():
#     ip='127.0.0.1'
#     ifaces=netifaces.interfaces()
#     ifaces.remove('lo')
#     for iface in ifaces:
#         addr=netifaces.ifaddresses(iface)
#         if 2 in addr:
#             ip=addr[2][0]['addr']
#     return ip

p=Peer(uuid1().hex,'127.0.0.1')
i=Inducter(('224.0.0.13',8999))
h=MessageHandler(p, i.broadcast)
i.addHandler(h.handle)
reactor.listenMulticast(8999,i)
reactor.run()
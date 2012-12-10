from LPDoL.TwLPD import *
from uuid import uuid1
import netifaces
from twisted.internet import reactor
ip='0.0.0.0'
ifaces=netifaces.interfaces()
ifaces.remove('lo')
for iface in ifaces:
    addr=netifaces.ifaddresses(iface)
    if 2 in addr:
        ip=addr[2][0]['addr']
p=Peer(uuid1().hex,ip)
i=Inducter(p,('224.0.0.13',8999))
reactor.listenMulticast(8999,i)
reactor.run()

#!/usr/bin/env python2
import os
import socket as sck
from TwLPD import *
import uuid
import sys
import socket
from netifaces import ifaddresses, interfaces, AF_INET
import logging
from twisted.internet import reactor

logging.basicConfig(level=logging.INFO)

def get_ip():
	for iface in interfaces():
		if_addr=ifaddresses(iface)
		if AF_INET in if_addr:
			addr=if_addr[AF_INET][0]['addr']
			if not addr=='127.0.0.1':
				return addr
	return ''

if __name__=='__main__':
	max_attempt=3
	n=0
	uid=str(uuid.uuid4())
	mcast=('224.1.23.24',15523)
	i=Inducter(uid, mcast)
	b=sck.socket(sck.AF_INET, sck.SOCK_DGRAM, sck.IPPROTO_UDP)
	b.setsockopt(sck.IPPROTO_IP, sck.IP_MULTICAST_TTL, 32)
	reactor.listenMulticast(15523, i, listenMultiple=True)
	reactor.run()
	while True:
		if not i.peer_list is None:
			print "Inducted"
			print i.peer_list
			break
		if n>max_attempt:
			p_o=Peer(uid,get_ip(),0)
			print "Creating FISH_NET"
			i.peer_list=set([p_o])
			break
		b.sendto('FISH_HOOK:{0}'.format(uid), mcast)
		n+=1
	while True:
		pass

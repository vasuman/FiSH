#!/usr/bin/env python2
import os
from TwLPD import *
import uuid
import sys
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

def shout(uid):
	if i.peer_list is None:
		shout.n+=1
		if shout.n>shout.max_attempt:
			print "Creating FISH_NET"
			i.peer_list=set([Peer(uid=uid, addr=get_ip(), index=0)])
		else:
			print "Broadcasting"
			i.broadcast()
			reactor.callLater(2,shout,(uid))
shout.n=0
shout.max_attempt=3
def cleanup():
	print i.peer_list

if __name__=='__main__':
	uid=str(uuid.uuid4())
	mcast=('224.1.23.24',15523)
	i=Inducter(uid, mcast)
	reactor.listenMulticast(15523, i, listenMultiple=True)
	reactor.callLater(1,shout,(uid))
	reactor.addSystemEventTrigger('before', 'shutdown', i.disconnect)
	reactor.addSystemEventTrigger('before', 'shutdown', cleanup)
	reactor.run()
	

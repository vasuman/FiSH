#!/usr/bin/env python2
import os
import socket as sck
from LPDoL import *
import uuid
import sys
import socket
from netifaces import ifaddresses, interfaces, AF_INET
import logging

logging.basicConfig(level=logging.INFO)

def create_fish_net(uid,mcast):
	self_obj=Peer(uid,get_ip(),0)
	i=Inducter(uid,mcast,[self_obj])
	return i

def get_ip():
	for iface in interfaces():
		if_addr=ifaddresses(iface)
		if AF_INET in if_addr:
			addr=if_addr[AF_INET][0]['addr']
			if not addr=='127.0.0.1':
				return addr
	return ''

if __name__=='__main__':
	uid=str(uuid.uuid4())
	mcast=('224.1.23.24',15523)
	try:
		b=Beacon(uid,mcast)
		b.burn(2)
		print b.peer_list
		
	except PeerDiscoveryError as e:
		if e.err is 4:
			print "No existing network creating a FISH_NET"
			i=create_fish_net(uid,mcast)
			i.start()
			try:
				while True: pass
			except KeyboardInterrupt:
				print i.addr_list
				i._stop.set()
		else:
			print e
			sys.exit(1)

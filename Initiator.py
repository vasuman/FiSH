import os
import socket as sck
from LPDoL import *
import uuid
import sys
import socket

def create_fish_net(uid,mcast):
	self_obj=Peer(uid,get_ip(),0)
	peer_list=[self_obj]
	i=Inducter(uid,mcast,peer_list)
	return i

def get_ip():
	s=socket.socket(socket.AF_INET,socket.SOCK_DGRAM)
	s.connect(('google.com',9))
	ip=s.getsockname()[0]
	s.close()
	return ip

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

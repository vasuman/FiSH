import threading
import struct
import pickle
import socket as sck
import os

class Peer(dict):
    def __init__(self, uid, ip_addr, p_index):
	self['uid']=uid
	self['ip']=ip_addr
	self['index']=p_index

    def __str__(self):
	return '{0[index]}: {0[ip]} - {0[uid]}'.format(self)

class PeerDiscoveryError(Exception):
    def __init__(self,code,msg):
	self.err=code
	self.msg=msg

    def __str__(self):
	return '{0}: {1}'.format(self.err,self.msg)

class Beacon():
	
	def __init__(self, uid, max_attempt, mcast, tcp_port):
		n=0
		(mcast_addr,mcast_port)=mcast
		self.tcp_port=tcp_port
		self.mcast_addr=mcast_addr
		self.mcast_port=mcast_port
		self.uid=uid
		while True:
			self.udp_broadcast()
			try:
				ip_list=self.get_peer_list(5)
				self.addr_list=ip_list
				break
			except PeerDiscoveryError as e:
				if e.err is 2:
					continue
				else:
					raise e
			if n>max_attempt:
				raise PeerDiscoveryError(4,'Maximum tries excceded')
			n+=1

	def udp_broadcast(self):
	    udp_sock=sck.socket(sck.AF_INET, sck.SOCK_DGRAM,sck.IPPROTO_UDP)
	    udp_sock.setsockopt(sck.IPPROTO_IP, sck.IP_MULTICAST_TTL, 32)
	    try:
	    	udp_sock.bind(('',self.mcast_port))
	    except sck.error as e:
	    	if x.errno is 98:
			raise PeerDiscoveryError(2,"Another process is using broadcast port")
		else:
			print e
	    msg='FISH_HOOK:{0}'.format(self.uid)
	    try:
	    	udp_sock.sendto(msg,(self.mcast_addr, self.mcast_port))
	    except sck.error as e:
	    	if x.errno is 101:
			raise PeerDiscoveryError(1,"Not connected to any network")
		else:
			print e
	    udp_sock.close()

	def get_peer_list(self, timeout):
	    tcp_sock=sck.socket(sck.AF_INET, sck.SOCK_STREAM)
	    tcp_sock.bind(('',self.tcp_port))
	    tcp_sock.listen(1)
	    tcp_sock.settimeout(timeout)
	    try:
		    con_sock,addr=tcp_sock.accept()
	    except sck.timeout:
	            tcp_sock.close()
		    raise PeerDiscoveryError(3,'Wait timed out')
	    ip_list=con_sock.recv(65536)
	    con_sock.close()
	    tcp_sock.close()
	    return ip_list


class Inducter(threading.Thread):
    def __init__(self, uid, mcast, addr_list):
    	super(Inducter,self).__init__()
	self._stop=threading.Event()
	self.addr_list=addr_list
	self.uid=uid
	(self.mcast_addr,self.mcast_port)=mcast
	self.udp_sock = sck.socket(sck.AF_INET, sck.SOCK_DGRAM, sck.IPPROTO_UDP)
	self.udp_sock.setsockopt(sck.SOL_SOCKET, sck.SO_REUSEADDR, 1)
	try:
		self.udp_sock.bind(('', self.mcast_port))
	except Exception as e:
		print e
	mem = struct.pack('4sl', sck.inet_aton(self.mcast_addr), sck.INADDR_ANY)
	self.udp_sock.setsockopt(sck.IPPROTO_IP, sck.IP_ADD_MEMBERSHIP, mem)
	self.udp_sock.settimeout(5)
	self.tcp_sock=sck.socket(sck.AF_INET, sck.SOCK_STREAM)

    def pI(self):
    	return True
    	extract_index=lambda x:self.addr_list[x]['index']
    	max_uid=max(self.addr_list,key=extract_index)
	return (max_uid==self.uid)

    def stop(self):
    	self._stop.set()

    def stopped(self):
    	return self._stop.isSet()

    def remove(self, e_uid):
    	del self.addr_list[e_uid]

    def induce(self, e_uid, addr):
    	last_index=self.addr_list.popitem()[1][2]
    	new_peer_obj=Peer(e_uid,addr[0],last_index+1)
	self.addr_list[uid]=new_peer_obj
	if self.pI():
		try:
			self.tcp_sock.connect((addr[0],self.tcp_port))
		except Exception as e:
			print e
		data_string=pickle.dumps(self.addr_list)
		self.tcp_sock.sendall(data_string)
    
    def run(self):
	extr_uid=lambda x:x[x.index(':')+1:]
	while True:
		if self.stopped():
			msg='FISH_UNHOOK:{0}'.format(self.uid)
			self.udp_sock.sendto(msg,(self.mcast_addr,self.mcast_port))
			self.udp_sock.close()
			self.tcp_sock.close()
			break
		try:
			msg,addr=self.udp_sock.recvfrom(1024)
		except sck.timeout:
			continue	
		if msg.startswith('FISH_HOOK:'):
			induce(extr_uid(msg),addr)
		elif msg.startswith('FISH_UNHOOK:'):
			remove(extr_uid(msg))

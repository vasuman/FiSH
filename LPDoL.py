import threading
import struct
import pickle
import socket as sck
import os

class Peer():
	'''A class that encapsulates all attributes of a fish node'''
	def __init__(self, uid, ip_addr, p_index):
		self.uid=uid
		self.ip=ip_addr
		self.index=p_index

	def __str__(self):
		return '{0.index}: {0.ip} - {0.uid}'.format(self)

class PeerDiscoveryError(Exception):
	'''Implements better error handling'''
	def __init__(self,code,msg):
		self.err=code
		self.msg=msg

	def __str__(self):
		return '{0}: {1}'.format(self.err,self.msg)

class MulticastSocket(sck.socket):
	'''An implementation of a multicast socket built on a standard UDP socket specifically for use in LPDoL'''
	def __init__(self,mcast):
		super(MulticastSocket,self).__init__(sck.AF_INET,sck.SOCK_DGRAM,sck.IPPROTO_UDP)
		(self.mcast_addr,self.mcast_port)=mcast
		self.setsockopt(sck.SOL_SOCKET, sck.SO_REUSEADDR, 1)
		self.setsockopt(sck.IPPROTO_IP, sck.IP_MULTICAST_TTL, 32)
		self.bind(('',self.mcast_port))
		mem = struct.pack('4sl', sck.inet_aton(self.mcast_addr), sck.INADDR_ANY)
		self.setsockopt(sck.IPPROTO_IP, sck.IP_ADD_MEMBERSHIP, mem)
		self.settimeout(5)
	
	def sendm(self,msg):
		return self.sendto(msg,(self.mcast_addr, self.mcast_port))
	
class Beacon():
	'''Broadcasts presence and listens for peer list'''
	def __init__(self, uid, mcast):
		self.uid=uid
		try:
			self.mc_sock=MulticastSocket(mcast)
		except sck.error as e:
			if e.errno is 98:
				raise PeerDiscoveryError(2,"Another process is using broadcast port")
			elif e.errno is 19:
				raise PeerDiscoveryError(5,'No connected interface')
			else:
				raise e
		
			
	def udp_broadcast(self):
		msg='FISH_HOOK:{0}'.format(self.uid)
		try:
			self.mc_sock.sendm(msg)
		except sck.error as e:
			if x.errno is 101:
				raise PeerDiscoveryError(1,"Not connected to any network")
			else:
				raise e

	def get_peer_list(self):
		e=PeerDiscoveryError(3,'No valid response')
		try:
			msg,addr=self.mc_sock.recvfrom(1024)
		except sck.timeout:
			raise e
		if msg.startswith('FISHEIS:'):
			self.peer_list=pickle.loads(msg[7:])
			self.addr_recv=addr
		else:
			raise e
	
	def burn(self, max_attempt):
		n=0
		while True:
			self.udp_broadcast()
			if n>max_attempt:
				self.mc_sock.close()
				raise PeerDiscoveryError(4,'Maximum tries excceded')
			try:
				self.get_peer_list()
				self.mc_sock.close()
				break
			except PeerDiscoveryError as e:
				if e.err is 3:
					n+=1
					continue
				else:
					self.mc_sock.close()
					raise e

class Inducter(threading.Thread):
	def __init__(self, uid, mcast, addr_list):
		super(Inducter,self).__init__()
		self._stop=threading.Event()
		self.addr_list=addr_list
		self.uid=uid
		try:
			self.mc_sock=MulticastSocket(mcast)
		except sck.error as e:
			if e.errno is 98:
				raise PeerDiscoveryError(2,"Another process is using broadcast port")
			else:
				raise e

	def stop(self):
		self._stop.set()

	def stopped(self):
		return self._stop.isSet()

	def remove_peer(self, e_uid):
		del self.addr_list[e_uid]

	def add_peer(self, e_uid, addr):
		last_index=self.addr_list[-1].index
		new_peer_obj=Peer(e_uid,addr[0],last_index+1)
		self.addr_list[e_uid]=new_peer_obj
	
	def extr_header(self,msg):
		return msg[msg.index(':')+1:]

	def run(self):
		while True:
			if self.stopped():
				msg='FISH_UNHOOK:{0}'.format(self.uid)
				self.mc_sock.sendm(msg)
				break
			try:
				msg,addr=self.udp_sock.recvfrom(1024)
			except sck.timeout:
				continue
			if msg.startswith('FISH_HOOK:'):
				self.add_peer(extr_header(msg),addr)
				if self.addr_list[-2].uid==self.uid:
					data_string=pickle.dumps(self.addr_list)
					self.mc_sock.sendm('FISHIES:{0}'.format(data_string))
			elif msg.startswith('FISH_UNHOOK:'):
				self.remove_peer(extr_header(msg))
		

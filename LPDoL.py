'''Local Peer Discovery over LAN'''
import threading
from struct import pack
from pickle import dumps, loads
import socket as sck
import logging

class Peer():
	'''A class that encapsulates all attributes of a fish node'''
	def __init__(self, uid, ip_addr, p_index):
		self.uid=uid
		self.ip=ip_addr
		self.index=p_index

	def __str__(self):
		return '{0.index}: {0.ip} - {0.uid}'.format(self)
	
	def __repr__(self):
		return 'PEER:{0.uid} at IP:{0.ip}'.format(self)

class PeerDiscoveryError(Exception):
	'''Implements better error handling'''
	def __init__(self,code,msg):
		self.err=code
		self.msg=msg

	def __str__(self):
		return '[ERROR {0.err}] {0.msg}'.format(self)

class MulticastSocket(sck.socket):
	'''An implementation of a multicast socket built on a standard UDP socket specifically for use in LPDoL'''
	def __init__(self,mcast):
		super(MulticastSocket,self).__init__(sck.AF_INET,sck.SOCK_DGRAM,sck.IPPROTO_UDP)
		(self.mcast_addr,self.mcast_port)=mcast
		self.setsockopt(sck.SOL_SOCKET, sck.SO_REUSEADDR, 1)
		self.setsockopt(sck.IPPROTO_IP, sck.IP_MULTICAST_TTL, 32)
		self.bind(('',self.mcast_port))
		mem = pack('4sl', sck.inet_aton(self.mcast_addr), sck.INADDR_ANY)
		self.setsockopt(sck.IPPROTO_IP, sck.IP_ADD_MEMBERSHIP, mem)
		self.settimeout(5)
		self.convo=[]
	
	def sendm(self,msg):
		return self.sendto(msg,(self.mcast_addr, self.mcast_port))

	def recvm(self,bufsize):
		m,a=self.recvfrom(bufsize)
		self.conv.append((m,a))
		return m,a
	
class Beacon():
	'''Broadcasts presence and listens for peer list'''
	def __init__(self, uid, mcast):
		self.uid=uid
		self.peer_list=[]
		try:
			self.mc_sock=MulticastSocket(mcast)
			logging.info('Initated a multicast socket')
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
			logging.info('Broadcasting beacon....')
		except sck.error as e:
			if e.errno is 101:
				raise PeerDiscoveryError(1,"Not connected to any network")
			else:
				raise e

	def get_peer_list(self):
		e=PeerDiscoveryError(3,'No valid response')
		try:
			msg,addr=self.mc_sock.recvm(1024)
			logging.info('Recieved a response')
		except sck.timeout:
			raise e
		if msg.startswith('FISHEIS:'):
			self.peer_list=loads(msg[7:])
			self.addr_recv=addr
			self.mc_sock.sendm('FISH_HOOKED:{0}'.format(self.uid))
		else:
			logging.info('Not a valid respone')
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
					logging.warning('Attempt {0} failed!'.format(n))
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
		self._init_peers={}
		try:
			self.mc_sock=MulticastSocket(mcast)
		except sck.error as e:
			if e.errno is 98:
				raise PeerDiscoveryError(2,"Another process is using broadcast port")
			else:
				raise e

	def induct(self, e_uid, addr):
		if not e_uid in self.init_peers:
			self._init_peers[e_uid]=1
		else:
			self._init_peers[e_uid]+=1
		c=self._init_peers[e_uid]
		if self.addr_list[-(c+1)].uid==self.uid or c is 4:
			logging.info('Inducting peer {0} at {1}'.format(e_uid,addr))
			data_string=dumps(self.addr_list)
			self.mc_sock.sendm('FISHIES:{0}'.format(data_string))
	
	def add_peer(self, e_uid, addr):
		last_index=self.addr_list[-1].index
		new_peer_obj=Peer(e_uid,addr[0],last_index+1)
		if not new_peer_obj in self.addr_list:
			self.addr_list.append(new_peer_obj)
	
	def extr_header(self,msg):
		return msg[msg.index(':')+1:]

	def resolve_conflict(self):
		pass
	
	def run(self):
		while True:
			if self._stop.isSet():
				msg='FISH_UNHOOK:{0}'.format(self.uid)
				self.mc_sock.sendm(msg)
				break
			try:
				msg,addr=self.mc_sock.recvfrom(1024)
				print msg
			except sck.timeout:
				continue
			if msg.startswith('FISH_HOOK:'):
				logging.info('Initiation request from {0}'.format(addr))
				self.add_peer(extr_header(msg),addr)
				self.induct(extr_header(msg),addr)
			elif msg.startswith('FISH_UNHOOK:'):
				logging.info('Peer {0} has left'.format(addr))
				del self.addr_list[e_uid]
			elif msg.startswith('FISH_HOOKED:'):
				del self._init_peers[extr_header(msg)]
			elif msg.startswith('FISHIES:'):
				br_pl=loads(extr_header(msg))
				if not br_pl == self.addr_list:
					self.resolve_conflict()

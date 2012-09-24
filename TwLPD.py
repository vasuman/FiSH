from twisted.internet.protocol import DatagramProtocol
from twisted.internet import reactor
import socket as sck
from pickle import dumps,loads
from collections import namedtuple, Counter

Peer=namedtuple('Peer','uid addr index')

class LPDoLError(Exception):
	def __init__(self, err, message):
		self.err=err
		self.message=message

class MessageException(LPDoLError):
	def __str__(self):
		return 'Invalid message - [ERROR {0.err}]: {0.message}'.format(self)

class PeerDiscoveryError(LPDoLError):
	def __str__(self):
		return 'Peer Discovery Failure - [ERROR {0.err}]: {0.message}'.format(self)
	
class Inducter(DatagramProtocol):
	def __init__(self, uid, mcast):
		self.uid=uid
		(self.mcast_addr,self.mcast_port)=mcast
		self.m_keys={'FISH_HOOK':self._induct,'FISH_UNHOOK':self._remove,
			'FISH_PL':self._list_m,'FISH_HOOKED':self._inducted}
		self._init_reqs=Counter()
		self.peer_list=None

	def startProtocol(self):
		self.transport.setTTL(32)
		# Join the multicast address, so we can receive replies:
	        self.transport.joinGroup(self.mcast_addr)
	
	def _induct(self, data, addr):
		extract_index=lambda x:x.index
		if self.addr_list is None:
			return
		max_index=max(self.addr_list, key=extract_index).index
		new_peer=Peer(uid=data, addr=addr, index=max_index+1)
		self.peer_list.add(new_peer)

		self._init_reqs[data]+=1
		reqs=self._init_reqs[data]
		poI=sorted(self.addr_list, key=extract_index)[-(reqs)]
		if poI.uid == self.uid or reqs is 3:
			data_str=pickle.dumps(self.addr_list)
			message='FISH_PL:{0}'.format(data_str)
			self.transport.write(message, (self.mcast_addr, self.mcast_port))

	def _inducted(self, data, addr):
		del self._init_reqs[data]
	
	def _list_m(self, data, addr):
		try:
			peer_list=pickle.loads(data)
			if not type(peer_list) is set:
				raise MessageException(3,'Invalid pickled object')
		except:
			raise MessageException(4,'Invalid pickling string')
		if self.peer_list is None:
			self.peer_list=peer_list
		elif self.peer_list != peer_list:
			self._conflict(peer_list, addr)
	
	def _conflict(self, x_p_list, addr):
		pass

	def _remove(self, data, addr):
		del self.addr_list[data]

	def datagramReceived(self, message, addr):
		if not ':' in message:
			raise MessageException(1,'Malformed message string')
		chop_msg=message.split(':')
		key,data=chop_msg[0],''.join(chop_msg[1:])
		if not key in self.m_keys:
			raise MessageException(2,'Invalid message key')
		self.m_keys[key](data, addr)

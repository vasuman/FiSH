from twisted.internet.protocol import DatagramProtocol
from twisted.internet import reactor
import socket as sck
from pickle import dumps,loads
from collections import namedtuple, Counter

Peer=namedtuple('Peer','uid addr index')

class LPDoLError(Exception):
	'''Base Error class -- all other exceptions inherot from this'''
	def __init__(self, err, message):
		self.err=err
		self.message=message

class MessageException(LPDoLError):
	'''Prevents mutated or malicious messages'''
	def __str__(self):
		return 'Invalid message - [ERROR {0.err}]: {0.message}'.format(self)

class PeerDiscoveryError(LPDoLError):
	def __str__(self):
		return 'Peer Discovery Failure - [ERROR {0.err}]: {0.message}'.format(self)
	
class Inducter(DatagramProtocol):
	'''The heart of LPD, the Inducter class is a UDP socket listening on a specific multicast group'''
	def __init__(self, uid, mcast):
		'''Initialize with the Unique ID of host and Multicast group'''
		self.uid=uid
		(self.mcast_addr,self.mcast_port)=mcast
		# Initialize message handling functions
		self.m_keys={'FISH_HOOK':self._induct,'FISH_UNHOOK':self._remove,
			'FISH_PL':self._list_m,'FISH_HOOKED':self._inducted}
		self._init_reqs=Counter()
		self.peer_list=None

	def startProtocol(self):
		self.transport.setTTL(32)
		# Join the multicast address, so we can receive replies:
	        self.transport.joinGroup(self.mcast_addr)

	def broadcast(self):
		'''Broadcasts a FISH_HOOK on Multicast group'''
		message='FISH_HOOK:{0}'.format(self.uid)
		self.transport.write(message, (self.mcast_addr, self.mcast_port))

	def _induct(self, data, addr):
		'''Peer induction relies on a fallback model -- if responsible peer fails
		precceding peer takes over'''
		extract_index=lambda x:x.index
		# Check if self in not yet inducted
		if self.peer_list is None:
			return
		max_index=max(self.peer_list, key=extract_index).index
		new_peer=Peer(uid=data, addr=addr, index=max_index+1)
		self.peer_list.add(new_peer)
		# Increment no. initialization requests 
		self._init_reqs[data]+=1
		reqs=self._init_reqs[data]
		# Find peer responsible for induction
		poI=sorted(self.peer_list, key=extract_index)[-(reqs)]
		# Respond if responsible or final requst of peer
		if poI.uid == self.uid or reqs is 3:
			data_str=pickle.dumps(self.peer_list)
			message='FISH_PL:{0}'.format(data_str)
			self.transport.write(message, (self.mcast_addr, self.mcast_port))

	def _inducted(self, data, addr):
		del self._init_reqs[data]
	
	def _list_m(self, data, addr):
		try:
			peer_list=pickle.loads(data)
			# Check for malicious code
			if not type(peer_list) is set:
				raise MessageException(3,'Invalid pickled object')
		except:
			raise MessageException(4,'Invalid pickling string')
		if self.peer_list is None:
			self.peer_list=peer_list
		# Check for confilcting peer lists
		elif self.peer_list != peer_list:
			self._conflict(peer_list, addr)
	
	def _conflict(self, x_p_list, addr):
		pass

	def _remove(self, data, addr):
		del self.peer_list[data]

	def datagramReceived(self, message, addr):
		if not ':' in message:
			raise MessageException(1,'Malformed message string')
		chop_msg=message.split(':')
		key,data=chop_msg[0],''.join(chop_msg[1:])
		if not key in self.m_keys:
			raise MessageException(2,'Invalid message key')
		self.m_keys[key](data, addr)

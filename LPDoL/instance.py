from LPDoL.common import Peer
from LPDoL.handler import MessageHandler
from LPDoL.multicast import Inducter
from twisted.internet import reactor
from uuid import uuid1
import logging
class PDModule(object):
	def __init__(self, mcast_addr, name, peer_container):
		peer_obj=Peer(uid=uuid1().hex, name=name, addr='127.0.0.1')
		self.mcast_iface=Inducter(mcast_addr)
		reactor.listenMulticast(mcast_addr[1], self.mcast_iface)
		self.m_handler=MessageHandler(peer_obj, (lambda x:x) , peer_container)
		self.m_handler.enabled=False

	def setEnable(self, enable):
		if(enable):
			logging.info('Peer Discovery is enabled')
			self.m_handler.setOutputStream(self.mcast_iface.broadcast)
			self.mcast_iface.addHandler(self.m_handler.handle)
			#Don't do anything if its already enabled
			if not self.m_handler.enabled:
				#Reset hook gap
				self.m_handler.resetAll()
		else:
			logging.info('Disabling Peer Discovery')
			try:
				self.m_handler.hook_ID.cancel()
			except:
				pass
			self.m_handler.unhook()
			self.m_handler.enabled=False
			self.m_handler.setOutputStream((lambda x:x))
			self.mcast_iface.addHandler(None)


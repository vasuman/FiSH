from PyQt4 import QtGui, QtCore
import math
from LPDoL.common import Peer
import uuid

def format_peer(item):
	return 'Name : {0}\nUID : {1}..{2}'.format(item.name,item.uid[:5],item.uid[-5:])


byte_metric={
	0:'',
	1:'K',
	2:'M',
	3:'G'
}

def met_size(size):
	size=str(size)
	metric=(len(size)-1)/3
	if metric <= 3:
		return (size+' ')[:-3*metric-1]+' '+byte_metric[metric]+'B'
	else: 
		return size[:-9]+' GB'


class PeerContainer(QtGui.QStandardItemModel):
	
	updated=QtCore.pyqtSignal()

	def __init__(self):
		super(PeerContainer,self).__init__()
		self.items=[]


	def add(self, peer_obj):
		flag=True
		for item in self.items:
			if item.addr == peer_obj.addr:
				flag=False
				if item != peer_obj:
					flag=True
					self.items.remove(item)
		if(flag):
			self.items.append(peer_obj)
			self.refresh()

	def refresh(self):
		self.clear()
		for item in self.items:
			qItem=QtGui.QStandardItem(item.addr)
			qItem.setToolTip(format_peer(item))
			self.appendRow(qItem)
		self.emit(QtCore.SIGNAL('updated()'))

	def discard(self, peer_obj):
		for item in self.items:
			if item.addr == peer_obj.addr:
				self.items.remove(item)
				self.refresh()

	def getAddrList(self):
		return [item.addr for item in self.items]

	def addAddr(self, addr):
		if self.isAtAddr(addr):
			return
		peer_obj=Peer(uid=uuid.uuid1().hex, name='1user', addr=addr)
		self.add(peer_obj)


	def isAtAddr(self, addr):
		for item in self.items:
			if addr == item.addr:
				return True
		return False

class FileIndexModel(QtGui.QStandardItemModel):
	def __init__(self):
		super(FileIndexModel, self).__init__()
		self.addrHT={}
		self.headers=['Name', 'Size', 'Hash', 'Peer IP']
		for idx, header in enumerate(self.headers, start=0):
			self.setHorizontalHeaderItem(idx, QtGui.QStandardItem(header))
		self.selAddr=''
		self.refresh()


	def refresh(self):
		self.removeRows(0, self.rowCount())
		if self.selAddr != '':
			self.populateIP(self.selAddr)
			return
		for addr in self.addrHT.iterkeys():
			self.populateIP(addr)

	def updateIndex(self, addr, fileHT):
		self.addrHT[addr]=fileHT
		self.refresh()

	def populateIP(self, addr):
		if not addr in self.addrHT:
			return
		fileHT=self.addrHT[addr]
		for hsh in fileHT.iterkeys():
			fName, fSize =fileHT[hsh]
			rowData=[QtGui.QStandardItem(field) for field in (fName, str(fSize), hsh, addr)]
			rowData[0].setToolTip(fName)
			rowData[1].setToolTip(met_size(fSize))
			rowData[2].setToolTip('SHA1: '+hsh)
			self.appendRow(rowData)

	def selectIP(self, addr):
		self.selAddr=addr

	def getAddrList(self):
		return self.addrHT.iterkeys()

	def delIndex(self, addr):
		del self.addrHT[addr]
		self.refresh()

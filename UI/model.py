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

inv_byte={v:k for k,v in byte_metric.items()}

def met_size(size):
	idx=0
	while size>1000 and idx<3:
		idx+=1
		size/=1000.0
	size=math.floor(size*100)/100
	return '{0} {1}B'.format(size, byte_metric[idx])

class PeerContainer(QtGui.QStandardItemModel):
	
	updated=QtCore.pyqtSignal()

	def __init__(self):
		super(PeerContainer,self).__init__()
		self.items=[]
		self.blacklist=[]


	def add(self, peer_obj):
		if peer_obj.addr in self.blacklist:
			return 2
			logging.debug('IP in blacklist. Ignoring..')
		flag=True
		for item in self.items:
			if item.addr == peer_obj.addr:
				flag=False
				if item != peer_obj:
					flag=True
					self.items.remove(item)
				break
		if(flag):
			self.items.append(peer_obj)
			self.refresh()
		return 0

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
			return 1
		peer_obj=Peer(uid=uuid.uuid1().hex, name='1user', addr=addr)
		return self.add(peer_obj)


	def isAtAddr(self, addr):
		for item in self.items:
			if addr == item.addr:
				return True
		return False

	def blacklistAddr(self, addr):
		if not addr in self.blacklist:
			self.blacklist.append(addr)
		if addr in self.getAddrList():
			for item in self.items:
				if item.addr==addr:
					self.discard(item)

	def clearBlacklist(self):
		self.blacklist=[]

class FileIndexModel(QtGui.QStandardItemModel):
	def __init__(self):
		super(FileIndexModel, self).__init__()
		self.addrHT={}
		self.headers=['Name', 'Size', 'Peer IP', 'Hash']
		for idx, header in enumerate(self.headers, start=0):
			self.setHorizontalHeaderItem(idx, QtGui.QStandardItem(header))
		self.selAddr=None
		self.refresh()

	def refresh(self):
		self.removeRows(0, self.rowCount())
		if self.selAddr != None:
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
			rowData=[QtGui.QStandardItem(field) for field in (fName, met_size(fSize), addr, hsh)]
			for idx, tTxt in enumerate([fName, str(fSize), '', 'SHA1: {0}'.format(hsh)], start=0):
				rowData[idx].setToolTip(tTxt)
			self.appendRow(rowData)

	def selectIP(self, addr):
		self.selAddr=addr
		self.refresh()

	def getAddrList(self):
		return self.addrHT.keys()

	def delIndex(self, addr):
		del self.addrHT[addr]
		self.refresh()

def get_byte_size(size_str):
	size_str=str(size_str)
	size, metric=size_str.split()
	metric=metric[:1]
	size=int(size)
	return size*inv_byte[metric]

FILE_LIST_MAP={
	0:str,
	1:get_byte_size,
	2:str,
	3:str
}

class TxtMapSortProxyModel(QtGui.QSortFilterProxyModel):
	def __init__(self, source_model, function_map):
		super(QtGui.QSortFilterProxyModel, self).__init__(source_model)
		self.fn_map=function_map

	def lessThan(self, left, right):
		fn=self.fn_map[left.column()]
		return fn(self.sourceModel().itemFromIndex(left).text())<fn(self.sourceModel().itemFromIndex(right).text())

class DownloadWidgetManager(object):
	def __init__(self, tableWidget):
		self.tWidget=tableWidget
		self.fMap={}
		self.watchList=[]
		self.tWidget.setColumnCount(4)
		self.tWidget.setHorizontalHeaderLabels(['File Name', 'Status', 'Completion', 'Speed'])
		self.timer=QtCore.QTimer()
		self.timer.timeout.connect(self.pollEngine)
		self.timer.start(100)
		self.STATE_STR={
			0:'Initiated...',
			1:'Requesting File...',
			2:'Downloading...'
		}
		self.prevState={}
		self.tCount={}

	def pollEngine(self):
		try:
			for FTProt in self.watchList:
				idx=self.fMap[id(FTProt)]
				self.updateRow(idx, id(FTProt), FTProt)
		except Exception as e:
			print e

	def updateRow(self, idx, idF, fProt):
		lastState, lastB = self.prevState[idF]
		if lastState != fProt.state:
			self.tWidget.item(idx, 1).setText(self.STATE_STR[fProt.state])
		if fProt.state == 2:
			comp_str='{0}/{1}'.format(met_size(fProt.fGot), met_size(fProt.fSize))
			self.tWidget.item(idx, 2).setText(comp_str)
			self.tWidget.item(idx, 3).setText(met_size((fProt.fGot)/(0.1*self.tCount[idF]))+'/s')
		self.prevState[idF]=(fProt.state, fProt.fGot)
		self.tCount[idF]+=1


	def addFTProtocol(self, name, FTProt):
		self.watchList.append(FTProt)
		idx=self.tWidget.rowCount()
		self.fMap[id(FTProt)]=idx
		self.prevState[id(FTProt)]=(-1, 0)
		self.tCount[id(FTProt)]=1
		self.tWidget.setRowCount(idx+1)
		for j, val in enumerate([name, 'Connecting..', '-', '0 B/s']):
			self.tWidget.setItem(idx, j, QtGui.QTableWidgetItem(val))
		return id(FTProt)

	def doneFT(self, idFT):
		if idFT in self.fMap.keys():
			row = self.fMap[idFT]
			self.tWidget.removeRow(row)
			del self.watchList[row]
			del self.fMap[idFT]
			del self.prevState[idFT]
			del self.tCount[idF]

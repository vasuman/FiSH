from PyQt4 import QtCore, QtGui
import sys
app=QtGui.QApplication(sys.argv)

import qt4reactor
qt4reactor.install()

from twisted.internet import reactor
from twisted.internet.defer import Deferred

from window import Ui_MainWindow
import icons_rc
from startup import *
import first_run
import model

import json
import uuid

from LPDoL.common import Peer
from LPDoL.instance import PDModule
from FiT import daemon, probe, indexer 

import logging

logging.basicConfig(level=logging.DEBUG)

SETTINGS_FILE='settings.json'

class UIController(QtGui.QMainWindow):
    def __init__(self, parent=None):
        #Loads of BORING UI setup code!!
        QtGui.QMainWindow.__init__(self, parent)
        self.ui=Ui_MainWindow()
        self.ui.setupUi(self)
        self.loadSettings()
        self.initPD()
        self.initFTD()
        self.ui.listView.setModel(self.peer_container)
        self.ui.listView.setEditTriggers(QtGui.QAbstractItemView.NoEditTriggers)
        self.ui.tableView.setModel(self.proxy)
        self.ui.tableView.setEditTriggers(QtGui.QAbstractItemView.NoEditTriggers)
        self.setResizePolicy()
        self.initConnection()    

    def setResizePolicy(self):
        header_crtl=self.ui.tableView.horizontalHeader()
        header_crtl.setResizeMode(0, QtGui.QHeaderView.Stretch)
        header_crtl.setResizeMode(1, QtGui.QHeaderView.ResizeToContents)
        header_crtl.setResizeMode(3, QtGui.QHeaderView.ResizeToContents)

    def initConnection(self):
        self.ui.actionDiscover.triggered.connect(self.setDiscover)
        self.ui.actionAddIP.triggered.connect(self.manAddIP)
        self.peer_container.updated.connect(self.updateHT)

    def initPD(self):
        self.busy_peers=[]
        self.peer_container=model.PeerContainer()
        mcast_addr=(self.settings['MULTICAST_IP'], int(self.settings['MULTICAST_PORT']))
        self.pd=PDModule(mcast_addr, self.settings['NAME'], self.peer_container)

    def initFTD(self):
        self.finxr=indexer.FileIndexer(self.settings['INDEXER_PATH'])
        self.dfct=daemon.IFFactory(self.finxr)
        reactor.listenTCP(int(self.settings['DAEMON_PORT']),self.dfct)
        self.file_model=model.FileIndexModel()
        self.proxy = QtGui.QSortFilterProxyModel(self)
        self.proxy.setSourceModel(self.file_model)


    def manAddIP(self):
        ipaddr, ok = QtGui.QInputDialog.getText(self, 'Manual IP Entry', 'IP address')
        if ok:
            ipaddr=str(ipaddr)
            if not is_valid_ip(ipaddr):
                QtGui.QMessageBox.warning(self,'Input Error','Invalid IP address')
                return
            self.peer_container.addAddr(ipaddr)

    def loadSettings(self):
        re_cd, self.settings=load_settings_from_file(SETTINGS_FILE)
        if re_cd:
            self.firstRun()
        save_settings_to_file(self.settings, SETTINGS_FILE)


    def isValidConfig(self):
        return is_name(self.settings['NAME']) and is_dir_path(self.settings['INDEXER_PATH'])

    def firstRun(self):
        self.settings=DEFAULT_SETTINGS
        frDialog=QtGui.QDialog(parent=self)
        frDialog.ui=first_run.Ui_Dialog()
        frDialog.ui.setupUi(frDialog)
        frDialog.ui.lineEdit.setText(self.settings['NAME'])
        def folderHandler():
            shareFolder=str(QtGui.QFileDialog.getExistingDirectory(frDialog,'Choose a directory to share'))
            frDialog.ui.lineEdit_2.setText(shareFolder)
            self.settings['INDEXER_PATH']=shareFolder
        frDialog.ui.pushButton.clicked.connect(folderHandler)
        frDialog.setFixedWidth(390)
        frDialog.setFixedHeight(175)
        frDialog.exec_()
        self.settings['NAME']=str(frDialog.ui.lineEdit.text())
        if not self.isValidConfig():
            QtGui.QMessageBox.critical(self,'Settings Error','Invalid Configuration')
            logging.critical('Invalid Config')
            exit_reactor(14)

    def updateHT(self):
        active_peers=self.peer_container.getAddrList()
        explored_peers=self.file_model.getAddrList()
        for item in explored_peers:
            if not item in active_peers:
                self.file_model.delIndex(item)
        for item in active_peers:
            if not item in explored_peers:
                self.discoverPeer(item)

    def gotHT(self, fileHT, addr):
        self.busy_peers.remove(addr)
        self.file_model.updateIndex(addr, fileHT)

    def discoverPeer(self, addr):
        if addr in self.busy_peers:
            return
        d=Deferred()
        d.addCallback(self.gotHT, addr)
        d.addErrback(self.logError, addr)
        self.busy_peers.append(addr)
        print addr in self.busy_peers
        reactor.connectTCP(addr, 17395, probe.FHFactory(d))
    
    def logError(self, reason, addr):
        if addr in self.busy_peers:
            self.busy_peers.remove(addr)
        logging.error('Error connecting to {0} : {1}', addr, str(reason))


    def setDiscover(self):
        self.pd.setEnable(self.ui.actionDiscover.isChecked())

def exec_main_app():
    inst=UIController()
    inst.show()
    reactor.runReturn()
    #Somehow the reactor doesn't trigger shutdown automatically?
    exit_reactor(app.exec_())


def exit_reactor(res):
    if reactor.running:
        #Manually firing shutdown triggers
        logging.info('Shutting down twisted reactor')
        reactor.fireSystemEvent('shutdown')
        reactor.stop()
    sys.exit(res)

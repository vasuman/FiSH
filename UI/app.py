from PyQt4 import QtCore, QtGui
import sys
app=QtGui.QApplication(sys.argv)

import qt4reactor
qt4reactor.install()

from twisted.internet import reactor
from twisted.internet.defer import Deferred

from window import Ui_MainWindow
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
        self.peerSelection=self.ui.listView.selectionModel()
        self.ui.tableView.setModel(self.proxy)
        self.fileSelection=self.ui.tableView.selectionModel()
        self.dloadMgr=model.DownloadWidgetManager(self.ui.tableWidget)
        self.uiFix()
        self.initConnection()    

    def listCtxtMenu(self, point):
        if not self.peerSelection.hasSelection():
            return
        menu=QtGui.QMenu(parent=self.ui.listView)
        menu.addAction(self.ui.actionExplore)
        menu.addAction(self.ui.actionBlacklistPeer)
        menu.exec_(self.ui.listView.mapToGlobal(point))

    def fileCtxtMenu(self, point):
        if not self.fileSelection.hasSelection():
            return
        menu=QtGui.QMenu(parent=self.ui.tableView)
        menu.addAction(self.ui.actionDownload)
        menu.addAction(self.ui.actionDownloadAs)
        menu.exec_(self.ui.tableView.mapToGlobal(point))
    
    def initConnection(self):
        self.ui.actionDiscover.triggered.connect(self.setDiscover)
        self.ui.actionAddIP.triggered.connect(self.manAddIP)
        self.ui.actionClearBlacklist.triggered.connect(self.peer_container.clearBlacklist)
        self.ui.actionBlacklistPeer.triggered.connect(self.blacklistPeer)
        self.ui.actionExplore.triggered.connect(self.explorePeer)
        self.peer_container.updated.connect(self.updateHT)
        self.ui.listView.customContextMenuRequested.connect(self.listCtxtMenu)
        self.ui.tableView.customContextMenuRequested.connect(self.fileCtxtMenu)
        self.ui.radioButton.toggled.connect(self.filterIP)
        self.ui.radioButton_2.toggled.connect(self.filterIP)
        self.ui.lineEdit.textChanged.connect(self.proxy.setFilterFixedString)
        self.peerSelection.selectionChanged.connect(self.filterIP)
        self.ui.actionDownload.triggered.connect(self.downloadAction)
        self.ui.actionDownloadAs.triggered.connect(self.downloadAsAction)

    def filterIP(self):
        if not self.ui.radioButton.isChecked():
            addr=self.getSelectedPeer()
            self.file_model.selectIP(addr)
        else:
            self.file_model.selectIP(None)

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
        self.proxy = model.TxtMapSortProxyModel(self, model.FILE_LIST_MAP)
        self.proxy.setFilterCaseSensitivity(QtCore.Qt.CaseInsensitive)
        self.proxy.setSourceModel(self.file_model)


    def manAddIP(self):
        ipaddr, ok = QtGui.QInputDialog.getText(self, 'Manual IP Entry', 'IP address')
        if ok:
            ipaddr=str(ipaddr)
            if not is_valid_ip(ipaddr):
                QtGui.QMessageBox.warning(self, 'Input Error', 'Invalid IP address')
                return
            rc=self.peer_container.addAddr(ipaddr)
            if rc == 1:
                QtGui.QMessageBox.information(self, 'Address Exception', 'IP is already present')
            elif rc == 2:
                QtGui.QMessageBox.warning(self, 'Address Exception', 'IP is blacklisted')

    def loadSettings(self):
        re_cd, self.settings=load_settings_from_file(SETTINGS_FILE)
        if re_cd:
            self.firstRun()
        save_settings_to_file(self.settings, SETTINGS_FILE)


    def isValidConfig(self):
        return is_name(self.settings['NAME']) and is_dir_path(self.settings['INDEXER_PATH'])

    def downloadAction(self):
        name, addr, fHash=self.getSelectedFile()
        option=QtGui.QMessageBox.question(self, 'Download file', 'Confirm download {0}'.format(name),\
            QtGui.QMessageBox.No | QtGui.QMessageBox.Yes)
        if option == QtGui.QMessageBox.Yes:
            sv_fObj=self.quickSaveFile(name)
            if sv_fObj:
                self.downloadFile(name, addr, fHash, sv_fObj)

    def downloadFile(self, name, addr, fHash, fObj):
        d=Deferred()
        fFact=probe.FTFactory(fHash, fObj, d)
        d.addCallback(self.makeDL, name)
        d.addErrback(self.logError, addr)
        reactor.connectTCP(addr, 17395, probe.FTFactory(fHash, fObj, d))

    def makeDL(self, FTProt, name):
        idx=self.dloadMgr.addFTProtocol(name, FTProt)
        FTProt.def_obj.addCallback(self.removeDL, idx)
        FTProt.def_obj.addErrback(self.removeDL, idx)

    def removeDL(self, arg, idFT):
        logging.info(arg)
        self.dloadMgr.doneFT(idFT)

    def downloadAsAction(self):
        name, addr, fHash=self.getSelectedFile()
        sv_fObj=self.saveFilePrompt(name)
        if sv_fObj:
            self.downloadFile(name, addr, fHash, sv_fObj)

    def saveFilePrompt(self, name):
        savePath=str(QtGui.QFileDialog.getSaveFileName(self, 'Choose a destination file', \
            os.path.join(self.finxr.path, 'tmp.'+name.split('.')[-1])))
        if savePath:
            return open(savePath, 'wb')
        return None

    def quickSaveFile(self, saveName):
        try:
            sv_fObj=None
            sv_fObj=self.finxr.saveFile(saveName)
        except:
            option=QtGui.QMessageBox.warning(self, 'File overwrite', 'File exits. Overwrite?', \
                QtGui.QMessageBox.Yes | QtGui.QMessageBox.Abort | QtGui.QMessageBox.Save)
            if option == QtGui.QMessageBox.Yes:
                return self.finxr.saveFile(saveName, True)
            elif option == QtGui.QMessageBox.Save:
                return self.saveFilePrompt(saveName)
        return sv_fObj

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
        frDialog.exec_()
        self.settings['NAME']=str(frDialog.ui.lineEdit.text())
        if not self.isValidConfig():
            QtGui.QMessageBox.critical(self,'Settings Error','Invalid Configuration')
            logging.critical('Invalid Config')
            exit_reactor(1)

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
        reactor.connectTCP(addr, 17395, probe.FHFactory(d))
    
    def logError(self, reason, addr):
        if addr in self.busy_peers:
            self.busy_peers.remove(addr)
        logging.error('Error connecting to {0} : {1}'.format(addr, str(reason)))

    def setDiscover(self):
        self.pd.setEnable(self.ui.actionDiscover.isChecked())

    def getSelectedPeer(self):
        if not self.peerSelection.hasSelection():
            return ''
        sIdx=self.peerSelection.selectedRows()[0]
        return str(self.peer_container.itemFromIndex(sIdx).text())

    def getSelectedFile(self):
        if not self.fileSelection.hasSelection():
            return None
        return [str(self.file_model.itemFromIndex(self.proxy.mapToSource(\
                self.fileSelection.selectedRows(column=idx)[0])\
                ).text()) for idx in [0,2,3]]

    def explorePeer(self):
        addr=self.getSelectedPeer()
        self.discoverPeer(addr)

    def blacklistPeer(self):
        addr=self.getSelectedPeer()
        self.peer_container.blacklistAddr(addr)

    def uiFix(self):
        header_crtl=self.ui.tableView.horizontalHeader()
        header_crtl.setResizeMode(0, QtGui.QHeaderView.Stretch)
        header_crtl.setResizeMode(1, QtGui.QHeaderView.ResizeToContents)
        header_crtl.setResizeMode(2, QtGui.QHeaderView.ResizeToContents)
        header_crtl=self.ui.tableWidget.horizontalHeader()
        header_crtl.setResizeMode(0, QtGui.QHeaderView.Stretch)
        header_crtl.setResizeMode(1, QtGui.QHeaderView.ResizeToContents)
        header_crtl.setResizeMode(2, QtGui.QHeaderView.ResizeToContents)



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

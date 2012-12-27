from FiT.common import *
from FiT.indexer import *
from FiT.daemon import *
from twisted.internet import reactor
import os
if __name__ == '__main__':
	if os.name == 'nt':
		path='C:\Users\Vasuman\Documents\FiSH'
	else:
		path='/home/vasuman/Documents/FiSH'
	reactor.listenTCP(17395, IFFactory(FileIndexer(path)))
	reactor.run()
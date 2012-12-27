from FiT.common import *
from FiT.indexer import *
from FiT.daemon import *
from twisted.internet import reactor
if __name__ == '__main__':
	reactor.listenSSL(17395, IFFactory(FileIndexer('/home/vasuman/Documents/FiSH')))
	reactor.run()
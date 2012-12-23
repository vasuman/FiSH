from FiT.common import *
from FiT.indexer import *
from FiT.daemon import *
from twisted.internet import reactor
reactor.listenTCP(17395, IFFactory(FileIndexer('/home/vasuman/Documents/FiSH')))
reactor.run()
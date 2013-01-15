from FiT.indexer import *
from FiT.daemon import *
from twisted.internet import reactor
import sys
import logging
if __name__ == '__main__':
	logging.basicConfig(level=logging.DEBUG)
	path=sys.argv[1]
	reactor.listenTCP(17395, IFFactory(FileIndexer(path)))
	reactor.run()
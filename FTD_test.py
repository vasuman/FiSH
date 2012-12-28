from FiT.indexer import *
from FiT.daemon import *
from twisted.internet import reactor
import sys
if __name__ == '__main__':
	path=sys.argv[1]
	reactor.listenTCP(17395, IFFactory(FileIndexer(path)))
	reactor.run()
#indexer.py
import os
from common import IndexerException
from hashlib import sha1

class FileIndexer(object)
    '''The FileIndexer class generates an index(dictionary) of all filenames 
    with their SHA1 checksums as keys and a tuple of (<filename>,<size>) as corresponding values
    The FileIndexer recursively traverses all subdirectories of main directory supplied'''
    def __init__(self, path):
    	if not os.path.exists(path):
    		raise IndexerException(1, 'Invalid path supplied')
    	if not os.path.isdir(path):
    		raise IndexerException(2,'Path is not directory')
    	self.path=os.path.abspath(path)
        self.index=self._generate_index()

    def _generate_index(self):
    	temp_index={}
    	for item in os.walk(self.path):
    		#Using 'don't CARE' condition '_'
    		base_dir, _, basenames=item
    		for basename in basenames:
    			filename=os.path.join(base_dir,basename)
    			#Skip broken symlinks!
    			if not os.path.exists(filename):
    				continue
    			file_size=os.stat(filename).st_size
    			#Generate SHA1 sum of file -- is kinda slow
    			with open(filename,'rb') as file_obj:
    				sha1sum=sha1(file_obj.read())
				temp_index[sha1sum]=[filename,file_size]
    	self.index=temp_index

    def getFile(fileIndex):
    	'''Returns a file object of the file at index opened in read mode'''
    	if not fileIndex in self.index:
    		raise IndexerException(3,'Invalid index supplied')
    	filename,_=self.index[fileIndex]
    	if not os.path.exists(filename):
    		raise IndexerException(4,'Directory structure has changed')
    	return open(filename, 'rb')
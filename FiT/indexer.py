#indexer.py
import logging
import os
from common import IndexerException
from hashlib import sha1
import json
from collections import namedtuple
import pickle

FileObject=namedtuple('FileObject', 'chksum path size')

CHKSUM=0
FNAME=1

class FileIndexer(object):
    '''The FileIndexer class generates two indexes(dictionary) of all filenames 
    with their SHA1 checksums and absolute pathnames as keys and a 
    file object of (<chksum>,<path>,<size>) as corresponding values
    The FileIndexer recursively traverses all subdirectories of main directory supplied'''
    def __init__(self, path):
        if not os.path.exists(path):
            raise IndexerException(1,'Invalid path supplied')
        if not os.path.isdir(path):
            raise IndexerException(2,'Path is not directory')
        self.path=os.path.abspath(path)
        try:
            self.hash_index, self.path_index=pickle.loads(self._open_prev_index())
            err=IndexerException(7,'Failed index integrity test')
            if len(self.hash_index) != len(self.path_index):
                logging.error('Index file lengths mismatch')
                raise err
            for value in self.path_index.values():
                if not value in self.hash_index.keys():
                    logging.error('Unreferenced keys exist')
                    raise err
            logging.info('Index file succeesfully loaded')
        except:
            self.hash_index, self.path_index={},{}
            logging.error('Error in loading index file')
        self._generate_index()
        logging.info('All files indexed')

    def _open_prev_index(self):
        index_file=os.path.join(self.path, '.findex')
        if not os.path.exists(index_file):
            logging.warn('No .findex found!!')
            raise IndexerException(6,'No existing index')
        return file(index_file,'rb').read()

    def _save_index(self):
        index_file=os.path.join(self.path, '.findex')
        with open(index_file,'wb') as fObj:
            fObj.write(pickle.dumps([self.hash_index, self.path_index]))
        logging.info('Index file written')

    def _generate_index(self):
        for item in os.walk(self.path):
            base_dir, _discard, basenames=item
            for basename in basenames:
                if basename == '.findex':
                    continue
                filename=os.path.join(base_dir,basename)
                #Skip broken symlinks!
                if not os.path.exists(filename):
                    continue
                file_size=os.stat(filename).st_size
                #Skip already indexed files
                if filename in self.path_index.keys():
                    sha1sum=self.path_index[filename]
                    #Check if the file has been updated
                    if self.hash_index[sha1sum].size == file_size:
                        continue
                    else:
                        self.delIndex(filepath=filename)
                #Generate SHA1 sum of file -- is kinda slow
                with open(filename,'rb') as file_obj:
                    sha1sum=sha1(file_obj.read()).hexdigest()
                if sha1sum in self.hash_index.keys():
                    continue
                ftObj=FileObject(chksum=sha1sum, path=filename, size=file_size)
                #Associate file hash with filename and size
                self.hash_index[sha1sum]=ftObj
                #Associate filename with hash
                self.path_index[filename]=sha1sum
        for filename in self.path_index.keys():
            if not os.path.exists(filename):
                self.delIndex(filepath=filename)
        self._save_index()


    def delIndex(self, filepath=None, chksum=None):
        if not filepath is None:
            chksum=self.path_index[filepath]
        elif not chksum is None:
            filepath=self.hash_index[chksum].name
        del self.hash_index[chksum]
        del self.path_index[filepath]


    def getFile(self, fileIndex):
        '''Returns a file object of the file at index opened in read mode'''
        if not fileIndex in self.hash_index.keys():
            raise IndexerException(3,'INVALID_FILE_ID')
        fhash, filename, file_size=self.hash_index[fileIndex]
        if not os.path.exists(filename) :
            self._generate_index()
            raise IndexerException(4,'DIR_CHANGED')
        with open(filename,'rb') as file_obj:
            sha1sum=sha1(file_obj.read()).hexdigest()
        if sha1sum != fileIndex:
            self._generate_index()
            raise IndexerException(8,'FILE_CHANGED')
        return open(filename, 'rb')

    def getFileSize(self, fileIndex):
        return self.hash_index[fileIndex].size

    def saveFile(self, fileName, overwrite=False):
        '''Returns a file like object to write data to in current directory'''
        filepath=os.path.join(self.path, fileName)
        if os.path.exists(filepath):
            if not overwrite:
                raise IndexerException(5,'File already exists')
        return open(filepath,'wb')

    def reduced_index(self):
        red_fn=lambda x:(os.path.basename(x.path), x.size)
        return json.dumps(dict([(k,red_fn(v)) for k,v in self.hash_index.iteritems()]))

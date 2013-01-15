#indexer.py
import logging
import os
from common import IndexerException
from hashlib import sha1
import json
from collections import namedtuple
import pickle

FileObject=namedtuple('FileObject', 'chksum name size')

CHKSUM=0
FNAME=1

class FileIndexer(object):
    '''The FileIndexer class generates two indexes(dictionary) of all filenames 
    with their SHA1 checksums as keys and a file object of (<chksum>,<filename>,<size>) as corresponding values
    The FileIndexer recursively traverses all subdirectories of main directory supplied'''
    def __init__(self, path):
        if not os.path.exists(path):
            raise IndexerException(1,'Invalid path supplied')
        if not os.path.isdir(path):
            raise IndexerException(2,'Path is not directory')
        self.path=os.path.abspath(path)
        try:
            self.index=pickle.loads(self._open_prev_index())
        except:
            self.index=[{},{}]
            logging.error('Failed to open index file')
        self._generate_index()
        logging.info('All files indexed')

    def _open_prev_index(self):
        index_fpath=os.path.join(self.path, '.findex')
        if not os.path.exists(index_fpath):
            logging.warn('No .findex found!!')
            raise IndexerException(9,'No existing index')
        return file(index_fpath,'rb').read()

    def _save_index(self):
        index_fpath=os.path.join(self.path, '.findex')
        with open(index_fpath,'wb') as fObj:
            fObj.write(pickle.dumps(self.index))

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
                if filename in self.index[FNAME].keys():
                    if self.index[FNAME][filename].size == file_size:
                        continue
                    else:
                        self.delIndex(filepath=filename)
                #Generate SHA1 sum of file -- is kinda slow
                with open(filename,'rb') as file_obj:
                    sha1sum=sha1(file_obj.read()).hexdigest()
                ftObj=FileObject(chksum=sha1sum, name=filename, size=file_size)
                #Associate file hash with filename and size
                self.index[CHKSUM][sha1sum]=ftObj
                self.index[FNAME][filename]=ftObj
        for filename in self.index[FNAME].keys():
            if not os.path.exists(filename):
                self.delIndex(filepath=filename)
        self._save_index()


    def delIndex(self, filepath=None, chksum=None):
        if not filepath is None:
            msg_d=self.index[FNAME][filepath].chksum
            del self.index[CHKSUM][msg_d]
            del self.index[FNAME][filepath]


    def getFile(self, fileIndex):
        '''Returns a file object of the file at index opened in read mode'''
        if not fileIndex in self.index[CHKSUM].keys():
            raise IndexerException(3,'INVALID_FILE_ID')
        filename, file_size=self.index[CHKSUM][fileIndex]
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
        return self.index[CHKSUM][fileIndex][1]

    def saveFile(self, fileName, overwrite=False):
        '''Returns a file like object to write data to in current directory'''
        file_path=os.path.join(self.path, fileName)
        if os.path.exists(file_path):
            if not overwrite:
                raise IndexerException(5,'File already exists')
        return open(file_path,'wb')

    def reduced_index(self):
        red_fn=lambda x:(os.path.basename(x[1]),x[2])
        return json.dumps(dict([(k,red_fn(v)) for k,v in self.index[CHKSUM].iteritems()]))

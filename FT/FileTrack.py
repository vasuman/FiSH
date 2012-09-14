import os
import sys

class FileObject(object):
	def __init__(self, abs_path, data=0):
		self.name=os.path.basename(abs_path)
		self.path=os.path.dirname(abs_path)
		self.ext=extension(self.name)
		if data:
			self.data=open(abs_path).read()

def extension(file_name):
	if not '.' in file_name :
		return ''
	if file_name[0]=='.':
		return ''
	return file_name[file_name.rindex('.')+1:]
	

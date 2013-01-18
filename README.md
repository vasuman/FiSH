#FiSH

A simple file transfer program that requires zero configuration. It discovers peers through IP Multicast and requires no central server to manage all connections. All communication is purely P2P.

##Dependancies
- [Twisted][twisted-python] - A web-framework for python


##Running 
In the main directory, run:
`$ python -m test.prompt /dir/to/sharing-folder`
All files in the specified directory will be shared.
On running, you will be presented with a prompt 

`>>`

Where you can enter commands that will be evaluated

####Commands
1.`list` - Lists *all* indexed files of *all* discovered peers

2.`refresh` - Re-indexes all files in the shared directory

3.`exit` - Exits safely!!

##Author
>Vasuman Ravichandran (<vasumanar@gmail.com>)

[twisted-python]:http://twistedmatrix.com/trac/
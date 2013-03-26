# FiSH 

Stands for 'Fi'le 'SH'aring.

A simple file transfer program that requires zero configuration. It discovers peers through IP Multicast and requires no central server to manage all connections. All communication is purely P2P.

## Dependencies
- [Twisted][twisted-python] - A web-framework for python

## Basic Concepts
* Each Peer is assigned a unique UID -- 16 byte string, and a name chosen by the user. From now on the string `<UID>.<name>` refers to the *"ident\_string"* of the peer the uniquely identifies each peer.

* Each peer joins a pre-determined multicast group.

* Peers discover each other through messages exchanged on this multicast group.
 
* Each peer maintains a local copy of discovered peers. Adding and removing peers managed by the multicast handler.

* Each peer also runs a file indexing daemon that recursively iterates over the files in a given folder, calculating the SHA1 hashes of each file and saving these values in an index.

* Each peer is also equipped with a probe.

* The probe retrieves the file hash index from any given peer and can also request a file transfer.

* A file transfer request from a probe is handled by the file transfer daemon.

## Modules

### LMessage
A custom message serialization module. Each message has to be instantiated with a context. I suggest that you create derived class whose constructor sets the *"context"* property of each object.

Each message has a *"code"* and a list which consists of *"data items"*. Each *"data item"* is a tuple consisting of multiple *"data members"*. This shallow fixed nesting is a result of the realization that two levels is as deep as it goes. 
Messages are represented as:-

`<message>` **:-:** `<key>:<items>`

`<items>` **:-:** `<item-1>;<item-2>;(..);<item-n>`

`<item>` **:-:** `<member-1>.<member-2>.(..).<member-n>`

Every message is base64 encoded on serialization. A message can be instantiated from a base64 encoded string on the transport endpoint

### LPDoL
Stands for Local Peer Discovery over LAN. It uses IP multicast to discover peers and broadcast its presence. There are 3 basic kinds of messages:-

1. **FISH\_HOOK** - This message is broadcast on an exponential back-off basis starting with a time interval of 1 second and each successive transmission delay is double the previous value. The first item consists of the *"ident\_string"* of the broadcasting peer followed by the ident\_string of all discovered peers - aimed at reducing redundant transmission. 

2. **FISH\_UNHOOK** - This message is triggered when the peer is about to exit.

3. **FISH\_LIVE** - Alerts all other peers of its existence, usually in response to a **FISH\_HOOK**

### FiT 
Stands for File Transfer. It consists of an indexer a daemon and a probe. 

+ **Indexer** - It recursively traverses a given directory and finds all files. The SHA1 checksum of each file is calculated and a file index is built. This index is stored in the root directory as a *".findex"* file. The indexer is also responsible for the creation of file containers for file downloads.

+ **Daemon** - It serves the file index to any requesting peer and also handles file uploads.

+ **Probe** - It fetches the file index of any peer and also retrieves _or_ downloads an indexed file.

Probe and daemon are based on a _StreamLineProtocol_. This is basically a LineReciever with some functionality to register custom data handlers to handle file transfer. 

The probe and daemon exchange file indexes and handle file transfers using 4 basic command srtings:-

1. **LOAD\_HASH\_TABLE** - It is a parameterless message sent from probe to daemon requesting the file index. The daemon dumps the file index as a JSON object on the open connection.

2. **LOAD\_FILE** - The probe requests the daemon to start file transfer of a file with given SHA1 hash. This is the first part of the threeway handshake that actually initiates file transfer

3. **START\_TRANSFER** - The daemon then replies with the size of the file in bytes, and the probe reponds with the desired byte range -- possible future support for parallel downloads.

4. **ERROR** - The daemon sends this message when it recieves an invalid command string. There a maximum of three invalid commands for each probe instance. 

## Running
In the main directory, run:

`$ python2.7 -m test.prompt /dir/to/sharing-folder`

All files in the specified directory will be shared.
On running, you will be presented with a prompt 

`>>`

Where you can enter commands that will be evaluated


## Author
> Vasuman Ravichandran (<vasumanar@gmail.com>)

[twisted-python]:http://twistedmatrix.com/trac/

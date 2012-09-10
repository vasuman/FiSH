#!/usr/bin/env python2

import socket as sck
import os

class PeerDiscoveryError(Exception):
    def __init__(self,code,msg):
        self.err=code
        self.msg=msg

    def __str__(self):
        return '{0}: {1}'.format(self.err,self.msg)

class Beacon(object):
	
	def __init__(self, uid, max_attempt, mcast, tcp_port):
		n=0
		(mcast_addr,mcast_port)=mcast
		while True:
			self.udp_broadcast(mcast_addr, mcast_port, uid)
			try:
				ip_list=self.listen_pl(5, tcp_port)
			except PeerDiscoveryError as e:
				if e.err is 2:
					continue
				else:
					raise e
			self.addr_list=ip_list
			if n>max_attempt:
				raise PeerDiscoveryError(1,'Maximum tries excceded')
			n+=1

	def udp_broadcast(self, mcast_addr, mcast_port, uid):
	    udp_sock=sck.socket(sck.AF_INET, sck.SOCK_DGRAM,sck.IPPROTO_UDP)
	    udp_sock.setsockopt(sck.IPPROTO_IP, sck.IP_MULTICAST_TTL, 32)
	    udp_sock.bind(('',mcast_port))
	    msg='FISH_HOOK:init:{0}'.format(uid)
	    udp_sock.sendto(msg,(mcast_addr, mcast_port))
	    udp_sock.close()

	def listen_pl(self, timeout, port):
	    tcp_sock=sck.socket(sck.AF_INET, sck.SOCK_STREAM)
	    tcp_sock.bind(('',port))
	    tcp_sock.listen(1)
	    tcp_sock.settimeout(timeout)
	    try:
		    tcp_sock.accept()
	    except sck.timeout:
	            tcp_sock.close()
		    raise PeerDiscoveryError(2,'Wait timed out')
	    ip_list=tcp_sock.recv(65536)
	    tcp_sock.close()
	    return ip_list


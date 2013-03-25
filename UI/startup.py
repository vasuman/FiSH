import logging
import json
import re
import os

#Multicast IP validation
VALID_MCAST_IP_RE=r'2(?:2[4-9]|3\d)(?:\.(?:25[0-5]|2[0-4]\d|1\d\d|[1-9]\d?|0)){3}'
VALID_IP_RE=r'^(([0-9]|[1-9][0-9]|1[0-9]{2}|2[0-4][0-9]|25[0-5])\.){3}([0-9]|[1-9][0-9]|1[0-9]{2}|2[0-4][0-9]|25[0-5])$'
def is_valid_ip(addr):
    if re.match(VALID_IP_RE, addr):
        return True
    return False

def is_mcast_ip(addr):
    if re.match(VALID_MCAST_IP_RE, addr):
        return True
    return False

def is_port(port):
    try:
        p_no=int(port)
    except:
        return False
    if p_no>65536 or p_no<0:
        return False
    return True

def is_dir_path(dir_path):
    try:
        if not os.path.isdir(dir_path):
            return False
    except:
        return False
    return True

def is_name(name_str):
    return len(name_str)<20


DEFAULT_SETTINGS={
    'MULTICAST_IP':'224.0.2.38',
    'MULTICAST_PORT':9387,
    'DAEMON_PORT':17395,
    'INDEXER_PATH':'',
    'NAME':'1user'
}

VALID_SETTINGS={
    'MULTICAST_IP':is_mcast_ip,
    'MULTICAST_PORT':is_port,
    'DAEMON_PORT':is_port,
    'INDEXER_PATH':is_dir_path,
    'NAME':is_name
}

def load_settings_from_file(fileName):
    if not os.path.exists(fileName):
        logging.warn('No Settings file')
        return (-1, {})
    with open(fileName, 'rb') as f:
        try:
            data=json.load(f)
        except:
            logging.error('Malformed settings file')
            return (-2, {})
    for key in VALID_SETTINGS.keys():
        try:
            if not VALID_SETTINGS[key](data[key]):
                logging.error('Invalid settings')
                return (-3, {})
        except Exception as e:
            logging.error('Setting key mismatch -- '+ str(e))
            return (-4, {})
    return (0, data)

def save_settings_to_file(settings, fileName):
    with open(fileName, 'wb') as f:
        json.dump(settings, f)

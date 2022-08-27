import subprocess
import socket
import platform

import os
import errno
import sys
import _thread
import time
import re
import configparser

import requests
import json
import sched
import random

from requests.adapters import HTTPAdapter
from requests.packages.urllib3.poolmanager import PoolManager


HTTP_OK = 200
PORTNUMBER = 50003
BRIDGEADDR = '192.168.1.140:8088'

SCANTYPE_IP = 1
SCANTYPE_ARP = 2
SCANTYPE_NONE = -1

CONFIGFILE = 'devstatmon.cfg'
LOGFILE = 'devstatmon.log'
DEVICE_LIST = []
PINGINTERVAL = 60


class logger(object):
	
	def __init__(self, toconsole, tofile, fname, append):
	
		self.toconsole = toconsole
		self.savetofile = tofile

		self.os = platform.system()
		if self.os == 'Windows':
			os.system('color')
		
		if tofile:
			self.filename = fname
			if not append:
				try:
					os.remove(fname)
				except:
					pass
			
	def __savetofile(self, msg):
		
		with open(self.filename, 'a') as f:
			f.write(f'{time.strftime("%c")}  {msg}\n')
	
	def __outputmsg(self, colormsg, plainmsg):
		
		if self.toconsole:
			print (colormsg)
		if self.savetofile:
			self.__savetofile(plainmsg)
	
	def info(self, msg):
		colormsg = f'\033[33m{time.strftime("%c")}  \033[96m{msg}\033[0m'
		self.__outputmsg(colormsg, msg)
		
	def warn(self, msg):
		colormsg = f'\033[33m{time.strftime("%c")}  \033[93m{msg}\033[0m'
		self.__outputmsg(colormsg, msg)
		
	def error(self, msg):
		colormsg = f'\033[33m{time.strftime("%c")}  \033[91m{msg}\033[0m'
		self.__outputmsg(colormsg, msg)
		
	def hilite(self, msg):
		colormsg = f'\033[33m{time.strftime("%c")}  \033[97m{msg}\033[0m'
		self.__outputmsg(colormsg, msg)
		
	def debug(self, msg):
		colormsg = f'\033[33m{time.strftime("%c")}  \033[37m{msg}\033[0m'
		self.__outputmsg(colormsg, msg)
		

class smartthingsdevice(object):
	
	def __init__(self, requestor, id, name, interval):
		
		self.requestor = requestor
		self.id = id
		self.name = name
		self.interval = interval
		self.state = 'unknown'
		self.laststate = 'unknown'
		self.lastupdate = time.time()

	def poll(self):

		url = 'https://api.smartthings.com/v1/devices/' + self.id + '/health'
		headers = {}
		headers['Authorization'] = 'Bearer ' + SMARTTHINGS_TOKEN
		headers['Host'] = 'api.smartthings.com'
		headers['Accept'] = '*/*'
		headers['User-Agent'] = 'devstatmon'

		try:
			
			r = requests.get(url, data='', headers=headers, timeout=5)
			
		except Exception as e:
				log.error (f"Request failed for device {self.id}: {e}")
				return
				
		if r.status_code == HTTP_OK:
			
			jsonresponse = json.loads(r.text)
			
			self.laststate = self.state
			
			if jsonresponse["state"] == 'ONLINE':
				self.state = 'present'
			else:
				if jsonresponse["state"] == 'OFFLINE':
					self.state = 'notpresent'
			
			log.info(f'Device <{self.id}> ({self.name}) returned {jsonresponse["state"]}')
			
			if (self.state != self.laststate) or ((time.time()-self.lastupdate) > 1800):
			
				log.info(f'\tUpdating SmartThings device "{self.name}" to {self.state}')
				BASEURL = f'http://{BRIDGEADDR}'

				requestor.send(BASEURL + '/' + self.name + '/presence/' + self.state)
				self.lastupdate = time.time()
			
			
		else:
			log.error (f'HTTP error returned: {r.status_code}')
			return

	def isonline(self):
		return self.state
		

class SourcePortAdapter(HTTPAdapter):
	""""Transport adapter" that allows us to set the source port."""
	def __init__(self, port, *args, **kwargs):
		self._source_port = port
		super(SourcePortAdapter, self).__init__(*args, **kwargs)

	def init_poolmanager(self, connections, maxsize, block=False):
		self.poolmanager = PoolManager(
			num_pools=connections, maxsize=maxsize,
			block=block, source_address=('', self._source_port))
			
			
class httprequest(object):
	
	def __init__(self, port):
		
		self.s = requests.Session()
		self.s.mount('http://', SourcePortAdapter(port))
	
	
	def send(self, url):

		HTTP_OK = 200
		
		host = re.search('//([\d.:]+)/', url).group(1)
		
		headers = { 'Host' : host,
					'Content-Type' : 'application/json'}
		
		oksent = False
	
		while oksent == False:
		
			try:
				r = self.s.post(url, headers=headers)
				
			except OSError as error:
				if OSError != errno.EADDRINUSE:
					log.error (error)
				else:
					log.error ("Address already in use; retrying")
				
				time.sleep(15)
			else:
				oksent = True

		if r.status_code != HTTP_OK:
			log.error (f'HTTP ERROR {r.status_code} sending: {url}')
#-----------------------------------------------------------------------
	
	
def periodic(scheduler, interval, action):
    scheduler.enter(interval, 1, periodic, (scheduler, interval, action))
    action()
	
############################### MAIN ###################################


CONFIG_FILE_PATH = os.getcwd() + os.path.sep + CONFIGFILE

parser = configparser.ConfigParser()
if not parser.read(CONFIG_FILE_PATH):
	print (f'\nConfig file is missing ({CONFIG_FILE_PATH})\n')
	exit(-1)
	
if parser.get('config', 'console_output').lower() == 'yes':
	conoutp = True	
else:
	conoutp = False

if parser.get('config', 'logfile_output').lower() == 'yes':
	logoutp = True
	LOGFILE = parser.get('config', 'logfile')
else:
	logoutp = False
	LOGFILE = ''
	
log = logger(conoutp, logoutp, LOGFILE, False)

devnamelist = parser.get('config', 'device_names')
devidlist = parser.get('config', 'device_ids')
polllist = parser.get('config', 'polling_interval')

SMARTTHINGS_TOKEN = parser.get('config','SmartThings_Bearer_Token')

devices = devidlist.split(',')
names = devnamelist.split(',')
pollintervals = polllist.split(',')

requestor = httprequest(PORTNUMBER)

i = 0
for device in devices:
	DEVICE_LIST.append(smartthingsdevice(requestor, device.strip(), names[i].strip(), int(pollintervals[i].strip())))
	i += 1
	
PORTNUMBER = int(parser.get('config', 'port'))
BRIDGEADDR = parser.get('config', 'bridge_address')

scheduler = sched.scheduler(time.time, time.sleep)

for device in DEVICE_LIST:
	periodic(scheduler, device.interval, device.poll)
	time.sleep(random.randint(10, 30))

scheduler.run()

try:
	while True:
		time.sleep(1)


except KeyboardInterrupt:
	log.warn ('\nAction interrupted by user...ending thread')


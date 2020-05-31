#!/usr/bin/python3
# -*- coding: UTF-8 -*-

import requests
import numpy as np
from random import choice,seed
from base64 import b64encode as encode
from base64 import b64decode as decode
import os
here = os.path.dirname(os.path.realpath(__file__))
HOME = os.getenv('HOME')

import logging
LG = logging.getLogger(__name__)
logging.getLogger("requests").setLevel(logging.WARNING)
logging.getLogger("urllib3").setLevel(logging.WARNING)


class profile(object):
   def __init__(self,IP='',hostname='',country='',state='',city='',
                                                         GPS_pos='',dates=[]):
      self.ip = IP
      self.hostname = hostname
      self.country = country
      self.state = state
      self.city = city
      self.coor = GPS_pos
      self.dates = dates
   def __str__(self):
      msg =  '       IP: %s\n'%(self.ip)
      msg += ' hostname: %s\n'%(self.hostname)
      msg += '  country: %s\n'%(self.country)
      msg += '    state: %s\n'%(self.state)
      msg += '     city: %s\n'%(self.city)
      msg += '      GPS: %s,%s\n'%(self.coor[0],self.coor[1])
      D = self.dates
      try: msg += '    dates: %s - %s (%s)'%(D[0],D[-1],len(D))
      except IndexError: msg = msg[0:-1]
      return msg

class myTimeOut(Exception):
    """ Auxiliary class to handle TimeOut from different libraries """
    pass


def analyze_IP(IP,lim=None):
   """ Randomly chooses a web service to look up the IP information """
   funcs = [ip_api,ipapi,ipinfo,tools_keycdn]  # Error in tools_keycdn
   if lim == None: lim = len(funcs)
   out,cont = False,0
   while not out or cont < lim:
      seed()
      f = choice(funcs)
      LG.info('Using api: %s for ip: %s'%(f.__name__,IP))
      try:
         resp = f(IP)
         return resp
      except myTimeOut: LG.warning('TimeOutError, try again (%s)'%(cont))
      cont += 1
   return None

def ipapi(IP,t0=3):
   """ Use webservice from ipapi.co to get information about an IP """
   url = 'https://ipapi.co/%s/json/'%(IP)
   LG.debug(url)
   try: location = requests.get(url, timeout=t0).json()
   except requests.exceptions.Timeout: raise myTimeOut
   hostname = ''
   ## country
   try: country = location['country']
   except: country = ''
   ## city
   try: city = location['city']
   except: city = ''
   ## State
   try: state = location['region']
   except: state = ''
   ## GPS position
   try:
      lat,lon = location['latitude'],location['longitude']
      GPS_pos = (float(lat),float(lon))
   except: GPS_pos = (0,0)
   return profile(IP,str(hostname),str(country),str(state),str(city),GPS_pos)


def ip_api(IP,t0=3):
   """ Use webservice from ip-api.com to get information about an IP """
   url = 'http://ip-api.com/json/%s'%(IP)
   LG.debug(url)
   try: location = requests.get(url, timeout=t0).json()
   except requests.exceptions.Timeout: raise myTimeOut
   ## hostname
   try: hostname = location['hostname']
   except: hostname = ''
   ## country
   try: country = location['country']
   except: country = ''
   ## city
   try: city = location['city']
   except: city = ''
   ## State
   try: state = location['region']
   except: state = ''
   ## GPS position
   try:
      lat,lon = location['lat'],location['lon']
      GPS_pos = (float(lat),float(lon))
   except: GPS_pos = (0,0)
   return profile(IP,str(hostname),str(country),str(state),str(city),GPS_pos)

def ipinfo(IP,t0=3):
   """ Use webservice from ipinfo.io to get information about an IP """
   url = 'http://ipinfo.io/%s'%(IP)
   LG.debug(url)
   try: location = requests.get(url, timeout=t0).json()
   except requests.exceptions.Timeout: raise myTimeOut
   ## hostname
   try: hostname = location['hostname']
   except: hostname = ''
   ## country
   try: country = location['country']
   except: country = ''
   ## city
   try: city = location['city']
   except: city = ''
   ## State
   try: state = location['region']
   except: state = ''
   ## GPS position
   try:
      aux = location['loc'].split(',')
      GPS_pos = (float(aux[0]),float(aux[1]))
   except: GPS_pos = (0,0)
   return profile(IP,str(hostname),str(country),str(state),str(city),GPS_pos)

import json
def tools_keycdn(IP,t0=3):
   """ Use webservice from tools.keycdn.com to get information about an IP """
   url = 'https://tools.keycdn.com/geo.json?host=%s'%(IP)
   LG.debug(url)
   #try: resp = requests.get(url, timeout=t0).json()
   #except requests.exceptions.Timeout: raise myTimeOut
   resp = os.popen('curl "%s"'%(url)).read().lstrip().rstrip()
   resp = json.loads(resp)
   ## hostname
   try: host = resp['data']['geo']['host']
   except: host = ''
   ## country
   try: country = resp['data']['geo']['country_code']
   except: country = ''
   ## city
   try: state = resp['data']['geo']['region']
   except: state = ''
   ## State
   try: city = resp['data']['geo']['city']
   except: city = ''
   ## GPS position
   try:
      lat = resp['data']['geo']['latitude']
      lon = resp['data']['geo']['longitude']
      GPS_pos = (float(lat),float(lon))
   except: GPS_pos = (0,0)
   return profile(IP,host,country,state,city,GPS_pos)


def get_url(markers=[],C_lat=None,C_lon=None,zoom=None,maptype='roadmap',
                                                 S=(600,300),force_path=False):
   """
      C_lat,C_lon : Center of the map. if not provided, use the center of
                    all markers
      markers: List of markers with format: Marker = (lat,lon,HUE_color)
      zoom: Zoom level (should be a function of the distance between markers)
      S:  size of the image
      maptype: Map type, options are: roadmap,terrain,hybrid,satellite
   """
   X = [M[0] for M in markers]
   Y = [M[1] for M in markers]
   if zoom != False:
      if len(markers) == 1 or np.mean([np.std(X),np.std(Y)]) < 0.75:
         # If only 1 point, or many points very close one to each other
         # then show a wide area to get an idea of the position (~ city level)
         zoom = 11
   sx,sy = S
   user,key = open('%s/api.private'%(here),'r').read().splitlines()
   key = str(decode(key),'utf-8')
   basic_url = 'https://maps.googleapis.com/maps/api/staticmap?'
   if C_lat!=None and C_lon!=None: basic_url += 'center=%s,%s'%(C_lat,C_lon)
   if zoom != None: basic_url += '&zoom=%s'%(zoom) #XXX make zoom automatic
   if zoom == False: pass
   basic_url += '&size=%sx%s'%(sx,sy)
   basic_url += '&maptype=%s'%(maptype)
   path = '&path=color:0x0000ff|'
   for M in markers:
      path += '%s,%s|'%(M[0],M[1])  # path
      #path += '%s,%s|'%(round(M[0],3),round(M[1],3))  # path
      #mark = '&markers=size:small|color:%s'%(M[2])+'%'   #
      try: mark = '&markers=size:small|color:%s'%(M[2])+'%'       #
      except IndexError: mark = '&markers=size:small|color:red%%' #
      mark += '7C%s,%s'%(M[0],M[1])                               # Markers
      basic_url += mark                                           #
   path = path[0:-1]  # remove last pipe
   aux = basic_url + '&key=%s'%(key) + path
   ## add path if possible
   if len(aux) <= 2000 and not force_path: basic_url += path
   basic_url += '&key=%s'%(key)
   if len(basic_url) > 2000: print('WARNING: URL probably too long')
   return basic_url


def get_map(url,fname='map.png'):
   """ Download map from url """
   import urllib
   opener = urllib.request.build_opener()  #XXX This will not work
   page = opener.open(url)
   my_picture = page.read()
   fout = open(fname, "wb")
   fout.write(my_picture)
   fout.close()


def maps_bike(start,end):
   las,los = start
   lae,loe = end
   user,key = open('%s/api.private'%(here),'r').read().splitlines()
   url = 'https://maps.googleapis.com/maps/api/directions/json?'
   url += 'origin=%s,%s&'%(las,los)
   url += 'destination=%s,%s&'%(lae,loe)
   url += 'mode=bicycling&key=%s'%(key)
   return url

def get_time(start,end):
   aux = urllib.request.urlopen(maps_bike(start,end)).read().decode('utf-8')
   data = json.loads(aux)
   ds = []
   for R in data['routes']:
      for l in R['legs']:
         ds.append( float(l['duration']['text'].split()[0]) )
   return min(ds)



if __name__ == "__main__":
   import logging
   #import log_help
   logging.basicConfig(level=logging.DEBUG,
                    format='%(asctime)s %(name)s:%(levelname)s - %(message)s',
                    datefmt='%Y/%m/%d-%H:%M:%S',
                    filename='geoip.log', filemode='w')
   LG = logging.getLogger('main')
   #log_help.screen_handler(LG)

   import argparse
   ## Get the options
   parser = argparse.ArgumentParser(description='Get Information about IP addresses')
   help_msg = 'Obtain a google maps url'
   parser.add_argument('-url',action='store_true', default=True, help=help_msg)
   help_msg = 'Download the map'
   parser.add_argument('-m',action='store_true',default=False, help=help_msg)
   parser.add_argument('IPs', nargs='*')
   args = parser.parse_args()

   ## Do the analysis
   coors = []
   for ip in args.IPs:
      IP = analyze_IP(ip)
      print(str(IP)+'\n') 
      coors.append(IP.coor)
   if args.url: print(get_url(markers=coors))
   if args.m: get_map(get_url(markers=coors))

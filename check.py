#!/usr/bin/python3
# -*- coding: UTF-8 -*-

import os
import re
import ipaddress as IP
import datetime as dt
import nmap
here = os.path.dirname(os.path.realpath(__file__))
HOME = os.getenv('HOME')
hostname = os.uname()[1]

dev_file = HOME+'/.devices.info'

now = dt.datetime.now()


class Device(object):
   def __init__(self,ip='',mac='',hostname='',ports=[]):
      if not isinstance(ip,list): self.ip = [ip]
      else: self.ip = ip
      self.mac = mac
      if hostname == '' and len(self.mac)>0:
         com = 'grep %s %s/macs.private'%(self.mac,here)
         known_mac = os.popen(com).read()
         known_mac = known_mac.lstrip().rstrip()
         if len(known_mac) > 0: 
            self.hostname = ' '.join(known_mac.split()[1:])
         else: self.hostname = 'Unknown'
      else: self.hostname = hostname
      try: self.ports = list(map(int,ports.split(',')))
      except: self.ports = []
   def __str__(self):
      msg = 'Host: '+ ', '.join(self.ip) + ' (%s)\n'%(self.hostname)
      msg += ' MAC: %s\n'%(self.mac)
      if len(self.ports) > 0:
         msg += 'Ports:'
         for p in self.ports:
            msg += ' %s'%(p)
         msg += '\n'
      return msg
   def __eq__(self,other):
      """ Overloading of the equality method """
      if isinstance(other, self.__class__):
         return self.mac == other.mac
      else: return False
   def __ne__(self, other):
      """ Overloading of the inequality method. Reduntant in python3? """
      return not self == other
   def save(self,fname):
      """
        Append the information of the device to a given file
      """
      f = open(fname,'a')
      ip = ','.join(self.ip)
      if self.hostname not in ['','Unknown']:
         f.write(ip+'   ' + ' (%s)\n'%(self.hostname))
      else: f.write(ip+'   '+self.mac+' (%s)\n'%(self.hostname))
      f.close()


def check_network(log=False):
   com = '/sbin/ifconfig | cut -d " " -f 1'  # -a ?
   interfaces = os.popen(com).read().split()
   interfaces = [x.replace(':','') for x in interfaces]
   interfaces.remove('lo')
   devices = []
   for I in interfaces:
      com = '/sbin/ifconfig %s'%(I)
      resp = os.popen(com).read().lstrip().rstrip()
      p =  r'(\w+): flags=(\S+)\s+mtu (\S+)\n'
      p += r'\s+inet (\S+.\S+.\S+.\S+)\s+netmask (\S+.\S+.\S+.\S+)\s+'
      p += r'broadcast (\S+.\S+.\S+.\S+)\n'
      m = re.search(p, resp)
      iface, flags, mtu, add, mask, Bcast  = m.groups()
      net = '.'.join(add.split('.')[0:-1])+'.0/'+mask
      net = IP.IPv4Network(net)
   
      ## Nmap. Fast discovery of alive hosts
      nm = nmap.PortScanner()
      nm.scan(net.exploded, arguments='-n -sP')
      # Store alive IPs
      ips_file = '/tmp/devices.txt'
      with open(ips_file,'w') as f:
         f.write('\n'.join(nm.all_hosts()))
      f.close()
      alive = ' '.join( nm.all_hosts() )
   
      ## Extract MAC of the alive devices
      os.system('fping -c1 -f %s > /dev/null 2> /dev/null'%(ips_file))
      os.system('rm %s'%(ips_file))
      resp = os.popen('/usr/sbin/arp -n | grep -v incomplete').read()
      IPs_MACs = []
      for l in resp.splitlines()[1:]:
         ip,_,mac,_,_ = l.split()
         IPs_MACs.append((ip,mac))
   
      ## IP-MAC dictionary
      ipmac = dict(IPs_MACs)
   
      ## Deep examination of hosts
      nm = nmap.PortScanner()
      nm.scan(alive, arguments='-Pn')
      for host in nm.all_hosts():
         try: hname = nm[host]['hostnames'][0]['name']
         except KeyError: hname = nm[host]['hostname'] # for deprecated version?
         except IndexError: hname = ''
         stat = nm[host].state()
         ports = ', '.join( map(str,nm[host].all_tcp()) )
         try: a = Device(ip=host,mac=ipmac[host],hostname=hname,ports=ports)
         except KeyError: a = Device(ip=host,mac='',hostname=hname,ports=ports)
         # Not duplicate devices with several IPs
         app = True
         for i_d in range(len(devices)):
            if a == devices[i_d]:
               devices[i_d].ip = list(set(devices[i_d].ip + a.ip))
               app = False
         if app: devices.append(a)
   
   ## Save report
   if log:
      msg = ''
      for d in devices:
         msg += now.strftime('%Y/%m/%d %H:%M')
         ip = ','.join(d.ip)
         msg += '   ' + ip
         if d.hostname not in ['','Unknown']:
            msg += '   (%s)\n'%(d.hostname)
         else: msg += '   (%s)\n'%(d.mac)
      f = open(dev_file+'.log','a')
      f.write(msg)
      f.close()
   else:
      # Initialize file
      f = open(dev_file,'w')
      f.write(now.strftime('%Y/%m/%d %H:%M')+'  @ %s\n'%(hostname))
      f.close()
      for d in devices:
         d.save(dev_file)
   return devices

if __name__ == '__main__':
   from argparse import ArgumentParser

   parser = ArgumentParser(description='Check devices connected to network')
   help_msg = 'Store data in log mode'
   parser.add_argument('-l',action='store_true',default=False, help=help_msg)

   args = parser.parse_args()

   devices = check_network(log=args.l)
   for d in devices:
      print(d)

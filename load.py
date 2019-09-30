#!/usr/bin/python3
# -*- coding: UTF-8 -*-

from configparser import ConfigParser, ExtendedInterpolation
from os.path import expanduser
import os
here = os.path.dirname(os.path.realpath(__file__))
HOSTNAME = os.uname()[1]


class Params(object):
   #def __init__(self, token_file, users_db, whitelist, log_file, pid_file):
   #   self.token_file = token_file
   #   self.users_db = users_db
   #   self.whitelist = whitelist
   #   self.log_file = log_file
   #   self.pid_file = pid_file
   def default(self):
      """
      This function should act as a default initialization either to generate
      ini templates or to replace missing initialization fields
      """
      self.token_file = here + '/' + HOSTNAME+'.token'
      self.users_db = here + '/users.db'
      self.whitelist = here + '/whitelist.private'
      self.log_file = here + '/' + HOSTNAME+'.log'
      self.pid_file = here + '/' + HOSTNAME+'.pid'
   def __str__(self):
      txt =  f'Token file: {self.token_file}\n'
      txt += f'  users_db: {self.users_db}\n'
      txt += f' whitelist: {self.whitelist}\n'
      txt += f'  log_file: {self.log_file}\n'
      txt += f'  pid_file: {self.pid_file}\n'
      return txt


def setup(fname='config.ini'):
   """ Parse the ini file and return a Params class """
   config = ConfigParser(inline_comment_prefixes='#')
   config._interpolation = ExtendedInterpolation()
   config.read(fname)

   P = Params()
   P.default()

   token_file = expanduser(config['bot']['token'])
   if token_file[0] != '/': token_file = here + '/' + token_file
   P.token_file = token_file

   users_db = expanduser(config['system']['users_db'])
   if users_db[0] != '/': users_db = here + '/' + users_db
   P.users_db = users_db

   whitelist = expanduser(config['system']['whitelist'])
   if whitelist[0] != '/': whitelist = here + '/' + whitelist
   P.whitelist = whitelist

   log_file = config['system']['log']
   if log_file.lower() == 'auto':
      log_file = here + '/' + HOSTNAME + '.log'
   else:
      log_file = expanduser(log_file)
      if log_file[0] != '/': log_file = here + '/' + log_file
   P.log_file = log_file

   pid_file = config['system']['pid']
   if pid_file.lower() == 'auto':
      pid_file = here + '/' + HOSTNAME + '.pid'
   else:
      pid_file = expanduser(pid_file)
      if pid_file[0] != '/': pid_file = here + '/' + pid_file
   P.pid_file = pid_file
   with open(P.pid_file,'w') as f:
      f.write(f'{os.getpid()}\n')
   return P


if __name__ == '__main__':
   import sys
   try: fname = sys.argv[1]
   except IndexError:
      print('File not specified')
      exit()

   P = setup(fname)

   print(P)

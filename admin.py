#!/usr/bin/python3
# -*- coding: UTF-8 -*-

import sqlite3
import csv
import logging
LG = logging.getLogger(__name__)


def read_from_csv(fname,headers=True):
   with open(fname) as csv_file:
      reader = csv.reader(csv_file, delimiter=',')
      if headers:
         headers = next(reader, None)
         headers = ','.join(headers)
      else: headers=''
      lines = []
      for l in csv.reader(csv_file, delimiter=','):
         lines.append(l)
   return lines, headers

def connect(sqlite_file='test.db'):
   """ Make connection to an SQLite database file """
   LG.info(f'Creating connection to {sqlite_file}')
   conn = sqlite3.connect(sqlite_file)
   c = conn.cursor()
   return conn, c

def create_db(conn, c, tname, field_types):
   """ Create SQLite database """
   #field_types = ','.join([f'{x} {y}' for x,y in zip(fields,types)])
   with conn:
      query = f"CREATE TABLE {tname} ({field_types})"
      try: c.execute(query)
      except sqlite3.OperationalError:
         LG.warning(f'Table {tname} already exists in DB')

def insert_usr(conn,c, chatid,uname,fname,lname,isadmin,table='users'):
   """
   Add user to database with fields:
                 chatid,username,first_name,last_name,is_admin
   """
   with conn:
      c.execute(f"INSERT INTO {table} VALUES (:pl0, :pl1, :pl2, :pl3, :pl4)",
                {'pl0': chatid, 'pl1': uname, 'pl2': fname,
                 'pl3': lname, 'pl4':isadmin})

def get_usr(conn,c,field,value,table='users'):
   with conn:
      c.execute(f"SELECT * FROM {table} WHERE {field}=:value",
                 {'value': value})
   return c.fetchall()

def update_usr(conn,c, uname, field, value,table='users'):
   with conn:
      c.execute(f"UPDATE {table} SET {field} = :value "+
                 "WHERE username = :username",
                 {'value': value, 'username': uname})

def remove_usr(conn,c, field,value,table='users'):
   with conn:
      c.execute(f"DELETE from {table} WHERE {field}=:value",{'value': value})

def get_info(conn,c, table='users'):
   with conn:
      lines = []
      for l in c.execute(f"PRAGMA table_info({table})").fetchall():
         lines.append(l)

def show_all(conn,c,table='users'):
   c.execute(f'SELECT * FROM {table}')
   names = list(map(lambda x: x[0], c.description))
   print(*names)
   rows = c.fetchall()
   for row in rows:
      print(*row)

if __name__ == '__main__':
   import sys
   try: fname = sys.argv[1]
   except IndexError: fname = 'users.data'
   
   if fname[-3:] == '.db':
      conn,c = connect(fname)
      show_all(conn,c)
   else:
      lines, ftypes = read_from_csv(fname)

      conn,c = connect('.'.join(fname.split('.')[:-1])+'.db')

      try: create_db(conn, c, 'users', ftypes)
      except sqlite3.OperationalError: pass

      for l in lines:
         rows = get_usr(conn,c, 'chatid', l[0], table='users')
         if len(rows)==0: insert_usr(conn, c, *l )
         else: print('Skipping',l[0])
      
      show_all(conn,c)
      print('--------------')
      # Cheatsheet
      #resp = get_usr(conn,c, 'username', '@n0w3l')
      #print(resp)

      #print('updating')
      #update_usr(conn,c, '@n0w3l', 'is_admin',True)
      #resp = get_usr(conn,c, 'username', '@n0w3l')
      #print(resp)

      #print('deleting')
      #remove_usr(conn,c, 'username', '@n0w3l')
      #resp = get_usr(conn,c, 'username', '@n0w3l')
      #print(resp)
      #conn.close()

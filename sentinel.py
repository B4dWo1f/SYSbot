#!/usr/bin/python3
# -*- coding: UTF-8 -*-

from threading import Thread
# Telegram-Bot libraries
from telegram import ChatAction, ParseMode
from telegram.ext import Updater, Filters
from telegram.ext import CommandHandler as CH #, MessageHandler, Filters
import datetime as dt
import os
here = os.path.dirname(os.path.realpath(__file__))
HOSTNAME = os.uname()[1]
HOME = os.getenv('HOME')
import logging
logging.basicConfig(level=logging.INFO,
                 format='%(asctime)s %(name)s:%(levelname)s - %(message)s',
                 datefmt='%Y/%m/%d-%H:%M',
                 filename=here+'/sentinel.log', filemode='w')
LG = logging.getLogger('main')
# My functions
import credentials as CR
import mycallbacks as cb
import admin


## Stop Bot ####################################################################
def shutdown():
   upt.stop()
   upt.is_idle = False

@CR.restricted
def stop(update, context):
   LG.info('Bot stopping')
   try: chatID = update['message']['chat']['id']
   except TypeError: chatID = update['callback_query']['message']['chat']['id']
   txt = 'I\'ll be shutting down\nI hope to see you soon!'
   M = context.bot.send_message(chatID, text=txt, parse_mode=ParseMode.MARKDOWN)
   Thread(target=shutdown).start()


## Reload Bot ##################################################################
def stop_and_restart():
   """
   Gracefully stop the Updater and replace the current process with a new one
   """
   upt.stop()
   os.execl(sys.executable, sys.executable, *sys.argv)

@CR.restricted
def restart(update,context):
   """ Gracefully reload the bot """
   LG.info('Bot restarting')
   try: chatID = update['message']['chat']['id']
   except TypeError: chatID = update['callback_query']['message']['chat']['id']
   txt = 'Bot is restarting...'
   context.bot.send_message(chatID, text=txt, parse_mode=ParseMode.MARKDOWN)
   Thread(target=stop_and_restart).start()

## Start bot ###################################################################
@CR.restricted
def start(update,context):
   """ Greet new users """
   #TODO report people joining here
   ch = update.message.chat
   msg = f'Joined @{ch.username} '
   msg += f'({ch.first_name} {ch.last_name}) '
   msg += f'in chat {ch.id}'
   LG.warning(msg)
   #with open('users.data','a') as f:
   #   f.write(f'{ch.id},@{ch.username},{ch.first_name},{ch.last_name},False\n')
   txt = "Welcome, this a test of a private bot"
   txt += ", don't blame me if it doesn't work for you ;p"
   context.bot.send_message(chat_id=update.message.chat_id, text=txt)
   # Register in database
   conn,c = admin.connect(dbfile)
   rows = admin.get_usr(conn,c, 'chatid', ch.id, table=table)
   if len(rows) == 0:
      LG.warning(f'Adding {ch.username} ({ch.id})')
      isadmin = ch.id in CR.ADMINS_id
      admin.insert_usr(conn,c, ch.id, ch.username, ch.first_name,
                                                   ch.last_name, isadmin)
   else: LG.info(f'User {ch.username} ({ch.id}) already registered')

def ready(context):
   """ on-boot greeting """
   LG.info('Bot is up')
   txt = 'Hi sir! ready for duty'
   context.bot.send_message(chatID, text=txt, disable_notification=True,
                                              parse_mode=ParseMode.MARKDOWN)


if __name__ == '__main__':
   import sys

   try: token = sys.argv[1]
   except IndexError:
      if os.path.isfile(here+f'/{HOSTNAME}.token'):
         token = here+f'/{HOSTNAME}.token'
      else:
         print('File not specified')
         exit()
   
   token, chatID = CR.get_credentials(token)

   # DataBase:
   field_types = ['chatid integer','username text','first_name text',
                  'last_name text','is_admin integer']
   dbfile = 'users.db'
   table = 'users'
   conn,c = admin.connect(dbfile)
   admin.create_db(conn, c, table, ','.join(field_types))
   conn.close()

   ## Define the Bot
   upt = Updater(token=token, use_context=True)
   dpt = upt.dispatcher
   jbq = upt.job_queue
   

   ## Add Handlers
   #sys handlers
   dpt.add_handler(CH('lock', cb.screen_lock))
   dpt.add_handler(CH('unlock', cb.screen_unlock, Filters.chat(CR.ADMINS_id)))

   #sentinel handlers
   dpt.add_handler(CH('screenshot',cb.screenshot, pass_job_queue=True))
   dpt.add_handler(CH('picture', cb.picture, Filters.chat(CR.ADMINS_id),
                                             pass_job_queue=True))
   dpt.add_handler(CH('sound', cb.sound, pass_job_queue=True,pass_args=True))
   dpt.add_handler(CH('recorddesktop', cb.recorddesktop, pass_job_queue=True))
   dpt.add_handler(CH('video', cb.video, Filters.chat(CR.ADMINS_id), pass_job_queue=True))
   dpt.add_handler(CH('where', cb.whereRyou, Filters.chat(CR.ADMINS_id)))
   dpt.add_handler(CH('wherelocal', cb.whereRyoulocal))
   dpt.add_handler(CH('whothere', cb.whoSthere))
   dpt.add_handler(CH('whoami', cb.whoami))
   dpt.add_handler(CH('who', cb.who))

   #admin handlers
   dpt.add_handler(CH('hola', cb.hola, pass_job_queue=True))
   dpt.add_handler(CH('reload', restart))
   dpt.add_handler(CH('stop', stop))
   dpt.add_handler(CH('pull', cb.pull,Filters.chat(CR.ADMINS_id)))
   dpt.add_handler(CH('top', cb.top,Filters.chat(CR.ADMINS_id),pass_args=True))
   dpt.add_handler(CH("start", start)) 
   

   now = dt.datetime.now()
   jbq.run_once(ready, now)

   ## Launch bot
   upt.start_polling()
   upt.idle()

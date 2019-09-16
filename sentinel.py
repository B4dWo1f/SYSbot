#!/usr/bin/python3
# -*- coding: UTF-8 -*-

from threading import Thread
# Telegram-Bot libraries
from telegram.ext import Updater
from telegram.ext import CommandHandler as CH #, MessageHandler, Filters
import os
here = os.path.dirname(os.path.realpath(__file__))
import logging
logging.basicConfig(level=logging.INFO,
                 format='%(asctime)s %(name)s:%(levelname)s - %(message)s',
                 datefmt='%Y/%m/%d-%H:%M',
                 filename=here+'/main.log', filemode='w')
LG = logging.getLogger('main')
# My functions
import credentials as CR
import mycallbacks as cb


## Stop Bot ####################################################################
def shutdown():
   upt.stop()
   upt.is_idle = False

@CR.restricted
def stop(bot, update):
   chatID = update.message.chat_id
   txt = 'I\'ll be shutting down\nI hope to see you soon!'
   M = bot.send_message(chatID, text=txt,
                        parse_mode='Markdown')
   Thread(target=shutdown).start()


## Reload Bot ##################################################################
def stop_and_restart():
   """
   Gracefully stop the Updater and replace the current process with a new one
   """
   upt.stop()
   os.execl(sys.executable, sys.executable, *sys.argv)

@CR.restricted
def restart(bot,update):
   txt = 'Bot is restarting...'
   chatID = update.message.chat_id
   bot.send_message(chat_id=chatID, text=txt, parse_mode='Markdown')
   Thread(target=stop_and_restart).start()


if __name__ == '__main__':
   import sys

   try: token = sys.argv[1]
   except IndexError:
      if os.path.isfile(here+'/RAVENsys.token'):
         token = here+'/RAVENsys.token'
      else:
         print('File not specified')
         exit()
   
   token, chatID= CR.get_credentials(token)

   ## Define the Bot
   upt = Updater(token=token)
   dpt = upt.dispatcher
   jbq = upt.job_queue
   

   ## Add Handlers
   #sys handlers
   dpt.add_handler(CH('lock', cb.screen_lock))

   #sentinel handlers
   dpt.add_handler(CH('screenshot',cb.screenshot, pass_job_queue=True))
   dpt.add_handler(CH('picture', cb.picture, pass_job_queue=True))
   dpt.add_handler(CH('sound', cb.sound))
   dpt.add_handler(CH('where', cb.whereRyou))
   dpt.add_handler(CH('whothere', cb.whoSthere))
   dpt.add_handler(CH('whoami', cb.whoami))
   dpt.add_handler(CH('who', cb.who))

   #admin handlers
   dpt.add_handler(CH('hola', cb.hola, pass_job_queue=True))
   dpt.add_handler(CH('reload', restart))
   dpt.add_handler(CH('stop', stop))
   

   ## Launch bot
   upt.start_polling()
   upt.idle()

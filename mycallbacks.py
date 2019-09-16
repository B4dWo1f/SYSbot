#!/usr/bin/python3
# -*- coding: UTF-8 -*-

from telegram import ChatAction
from threading import Thread
from random import choice
import tools
import geoip
import check
import os
import credentials as CR

## Action functions
def call_delete(bot, job):
   """ Delets a message. The message has to be provided in job.context """
   chatID = job.context['chat']['id']
   msgID = job.context['message_id']
   bot.delete_message(chatID,msgID)

def send_picture(bot, chatID, job_queue, pic, msg='',
                                    t=60,rm=False,delete=True,dis_notif=False):
   """
     Send a picture and, optionally, remove it locally/remotely (rm/delete)
     msg = caption of the picture
     t = time to wait to delete the remote picture
     rm = remove local file
     delete = remove remote file
   """
   if pic[:4] == 'http': photo = pic
   else: photo = open(pic, 'rb')  # TODO raise and report if file not found
   bot.send_chat_action(chat_id=chatID, action=ChatAction.UPLOAD_PHOTO)
   M = bot.send_photo(chatID, photo, caption=msg,
                                  timeout=300, disable_notification=dis_notif)
   if rm: os.system('rm %s'%(pic))
   if delete: job_queue.run_once(call_delete, t, context=M)
   return M

def send_sound(bot,chatID,job_queue,audio,msg='',t=10,rm=True,delete=True):
   mp3 = open(audio, 'rb')
   bot.send_chat_action(chat_id=chatID, action=ChatAction.UPLOAD_AUDIO)
   bot.send_audio(chatID, mp3, caption=msg,timeout=50)
   if rm: os.system('rm %s'%(audio))
   if delete: job_queue.run_once(call_delete, t, context=M)


## Sentinel functions
@CR.restricted
def screenshot(bot,update,job_queue):
   """
   Take a screenshot and send it
   """
   chatID = update.message.chat_id
   pic = '/tmp/screenshot.jpg'
   com = 'scrot -z %s'%(pic)
   os.system(com)
   txt = 'Please be patient, this usually takes a few seconds'
   M = bot.send_message(chatID, text=txt,parse_mode='Markdown')
   send_picture(bot,chatID,job_queue,pic,msg='Here it is the screenshot',t=10)
   bot.delete_message(chatID,M['message_id'])

@CR.restricted
def picture(bot,update,job_queue):
   """
   Take a picture from the webcam and send it
   ffmpeg args:
   -y: automatic overwrite
   -v 0: quiet, verbose = 0
   """
   chatID = update.message.chat_id
   devices = os.popen('ls /dev/video*').read().strip().splitlines()
   txt = 'Taking a picture from %s devices'%(len(devices))
   bot.send_message(chatID, text=txt,parse_mode='Markdown')
   for dev in devices:
      pic = '/tmp/out.jpg'
      com = 'ffmpeg -y -v 0 -f video4linux2 -s 1280x720 -i %s -ss 0:0:5'%(dev)
      com += ' -frames 1 %s'%(pic)
      os.system(com)
      txt = 'Picture from %s'%(dev)
      send_picture(bot,chatID,job_queue,pic,msg=txt,t=10,delete=True)

@CR.restricted
def sound(bot,update):
   """ Record and send audio from computers microphone """
   chatID = update.message.chat_id
   f = '/tmp/recording.mp3'
   com = 'sox -t alsa default %s silence 1 0.1 1%% 1 1.0 5%%'%(f)
   os.system(com)
   send_sound(bot,chatID,f)
   bot.send_message(chatID, text='Recorded sound',parse_mode='Markdown')

def whereRyou(bot,update):
   """ Return the IP where the bot is running """
   chatID = update.message.chat_id
   bot.send_chat_action(chat_id=chatID, action=ChatAction.TYPING)
   ip = tools.get_public_IP()
   txt = ''
   for l in str(geoip.analyze_IP(ip)).splitlines():
      txt += l.strip() + '\n'
   bot.send_message(chatID, text=txt[:-1],parse_mode='Markdown')

def whereRyoulocal(bot,update):
   """ Return the local IP where the bot is running """
   chatID = update.message.chat_id
   bot.send_chat_action(chat_id=chatID, action=ChatAction.TYPING)
   ips = os.popen('hostname -I').read().strip().split()
   txt = 'My local IP:\n'+' '.join(ips)
   bot.send_message(chatID, text=txt,parse_mode='Markdown')

@CR.restricted
def whoSthere(bot,update):
   """ Return all the devices connected to the bot's network """
   chatID = update.message.chat_id
   txt = 'Hold on, it might take a second'
   bot.send_message(chatID, text=txt,parse_mode='Markdown')
   bot.send_chat_action(chat_id=chatID, action=ChatAction.TYPING)
   txt = ''
   for d in check.check_network():
      l = ''
      for ld in str(d).strip().splitlines():
         l += ld.strip() + '\n'
      l = l.strip().replace('*',' ').replace('_',' ')
      l = l.replace('(','(*').replace(')','*)')
      txt += l + '\n--\n'
   bot.send_message(chatID, text=txt[:-2],parse_mode='Markdown')

def whoami(bot,update):
   """ echo-like service to check system status """
   chatID = update.message.chat_id
   ch = update.message['chat']
   txt = 'username: %s %s\n'%(ch['first_name'],ch['last_name'])
   txt += 'username: %s \n'%(ch['username'])
   txt += 'id: %s'%(ch['id'])
   bot.send_message(chat_id=chatID, text=txt, parse_mode='Markdown')

@CR.restricted
def who(bot,update):
   """ echo-like service to check system status """
   chatID = update.message.chat_id
   ch = update.message['chat']
   txt = 'Users in the computer:\n'
   txt += os.popen('who -s').read().strip()
   bot.send_message(chatID, text=txt, parse_mode='Markdown')

## Admin functions
def hola(bot, update, job_queue):
   """ echo-like service to check system status """
   chatID = update.message.chat_id
   salu2 = ['What\'s up?', 'Oh, hi there!', 'How you doin\'?', 'Hello!']
   txt = choice(salu2)
   M = bot.send_message(chatID, text=txt,
                        parse_mode='Markdown')

def screen_lock(bot,update):
   """ Lock the computer """
   chatID = update.message.chat_id
   com = 'gnome-screensaver-command --lock'
   os.system(com)
   bot.send_message(chat_id=chatID, text='Screen locked',
                    disable_notification=True, parse_mode='Markdown')

def conference_mode(bot,update):
   """
   Put the laptop in conference mode:
   - low brightness
   - restricted crontab
   - default background
   """
   chatID = update.message.chat_id
   com = 'xrandr --output `xrandr -q | grep " connected" | cut -d " " -f 1` --brightness 0.1'
   os.system(com)
   bot.send_message(chat_id=chatID, text='Done',
                    disable_notification=True, parse_mode='Markdown')


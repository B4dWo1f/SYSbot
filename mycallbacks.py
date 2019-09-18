#!/usr/bin/python3
# -*- coding: UTF-8 -*-

from telegram import ChatAction, ParseMode
from threading import Thread
from random import choice
import tools
import geoip
import check
import os
here = os.path.dirname(os.path.realpath(__file__))
import credentials as CR

## Action functions
def call_delete(bot, job):
   """ Delets a message. The message has to be provided in job.context """
   chatID = job.context['chat']['id']
   msgID = job.context['message_id']
   bot.delete_message(chatID,msgID)

def send_picture(bot, chatID, job_queue, pic, msg='',
                                   t=100,rm=False,delete=True,dis_notif=False):
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
   txt = 'sending audio, it may take a few seconds'
   M1 = bot.send_message(chatID, text=txt, parse_mode='Markdown')
   job_queue.run_once(call_delete, t, context=M1)
   bot.send_chat_action(chat_id=chatID, action=ChatAction.UPLOAD_AUDIO)
   M = bot.send_audio(chatID, mp3, caption=msg,timeout=50)
   if rm: os.system('rm %s'%(audio))
   if delete: job_queue.run_once(call_delete, t, context=M)

def send_video(bot, chatID, job_queue, vid, msg='',t=60,
               rm=False,delete=True,dis_notif=False,warn_wait=True):
   func = bot.send_video
   if vid[:4] == 'http': video = vid
   else:
      try:
         video = open(vid, 'rb')  # TODO raise and report if file not found
         if warn_wait:
            txt = 'This usually takes a few seconds... be patient'
            M1 = bot.send_message(chatID, text=txt, parse_mode='Markdown')
            job_queue.run_once(call_delete, 55, context=M1)
      except:
         video = vid
         func = bot.send_animation
   bot.send_chat_action(chat_id=chatID, action=ChatAction.UPLOAD_VIDEO)
   M = func(chatID, video, caption=msg,
                              timeout=300, disable_notification=dis_notif,
                              parse_mode=ParseMode.MARKDOWN)
   if rm: os.system('rm %s'%(vid))
   if delete:
      #LG.debug('pic %s to be deleted at %s'%(vid,dt.datetime.now()+dt.timedelta(seconds=t)))
      job_queue.run_once(call_delete, t, context=M)
   return M


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
def sound(bot,update,args,job_queue):
   """ Record and send audio from computers microphone """
   chatID = update.message.chat_id
   try: N = float(args[0])
   except: N=10
   fname = '/tmp/recording.mp3'
   #com = 'sox -t alsa default %s silence 1 0.1 1%% 1 1.0 5%%'%(f)
   com = f'sox -t alsa default {fname} trim 0 {N}'
   os.system(com)
   send_sound(bot,chatID,job_queue,fname,t=120,rm=True,delete=True)

@CR.restricted
def recorddesktop(bot,update,job_queue):
   """
    Starts and stops recording the desktop where the bot is running
   """
   chatID = update.message.chat_id
   def IsRunning():
      resp = os.popen('ps -e | grep recordmydesktop').read()
      if len(resp) == 0: return False
      else: return True
   fname = '/tmp/desktop.ogv'
   is_running = IsRunning()
   if is_running:
      txt = 'Stopping "recordmydesktop"'
      bot.send_message(chatID, text=txt,parse_mode='Markdown')
      os.system('killall recordmydesktop')
      while IsRunning():
         pass
      fname_new = '.'.join(fname.split('.')[:-1]) + '.mp4'
      convert = f'ffmpeg -y -i {fname} -vcodec mpeg4 -threads 2 '
      convert += f'-b:v 1500k -acodec libmp3lame -ab 160k '
      convert += f"{fname_new}"
      os.system(convert)
      send_video(bot, chatID, job_queue, fname_new, rm=True)
      os.system(f'rm {fname}')
   else:
      txt = 'Starting "recordmydesktop"'
      bot.send_message(chatID, text=txt,parse_mode='Markdown')
      com = 'recordmydesktop --on-the-fly-encoding'
      silent = ' --no-sound -o '
      com = com + silent + fname + ' &'
      os.system(com)

@CR.restricted
def video(bot,update,job_queue):
   """
    Starts and stops recording video where the bot is running
   """
   chatID = update.message.chat_id
   def IsRunning():
      resp = os.popen('ps -e | grep ffmpeg').read()
      if len(resp) == 0: return False
      else: return True
   fname = '/tmp/output.ogv'
   is_running = IsRunning()
   if is_running:
      txt = 'Stop recording'
      bot.send_message(chatID, text=txt,parse_mode='Markdown')
      os.system('killall -9 ffmpeg')
      while IsRunning():
         pass
      fname_new = '.'.join(fname.split('.')[:-1]) + '.mp4'
      convert = f'ffmpeg -loglevel quiet -y -i {fname} -vcodec mpeg4 '
      convert += f'-threads 2 '
      convert += f'-b:v 1500k -acodec libmp3lame -ab 160k '
      convert += f"{fname_new}"
      os.system(convert)
      send_video(bot, chatID, job_queue, fname_new, rm=True)
      os.system(f'rm {fname}')
   else:
      txt = 'Start recording'
      bot.send_message(chatID, text=txt,parse_mode='Markdown')
      com = 'ffmpeg -y -loglevel quiet -f v4l2 -framerate 25 '
      com += '-video_size 1280x720 -i /dev/video0 '
      #com += '-t 00:00:20 '
      com += fname + ' &'
      os.system(com)

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

@CR.restricted
def screen_unlock(bot,update):
   """ Lock the computer """
   chatID = update.message.chat_id
   com = 'gnome-screensaver-command -d'
   os.system(com)
   bot.send_message(chat_id=chatID, text='Screen unlocked',
                    disable_notification=True, parse_mode='Markdown')

@CR.restricted
def pull(bot,update):
   """ On-demand git pull DANGEROUS!!! """
   chatID = update.message.chat_id
   com = f'cd {here} && git pull'
   txt = os.popen(com).read().strip()
   txt = '`' + txt + '`'
   bot.send_message(chat_id=chatID, text=txt,
                    disable_notification=True, parse_mode='Markdown')

def top(bot,update,args):
   """ Return the first n lines of top command """
   chatID = update.message.chat_id
   try: N = int(args[0])
   except: N = 7   # TODO enter ir as argument
   tmp = '/tmp/top.txt'
   com = f'top -b -n 3 > {tmp} '
   com += f'&& tail -n +6 {tmp} && rm {tmp}'
   top = os.popen(com).read().strip()
   keep = []
   for l in top.splitlines()[:N]:
      ll = l.split()
      l0='%6s %5s %5s %5s %9s %5s'%(ll[0], ll[1], ll[8], ll[9], ll[10], ll[11])
      keep.append(l0)
   top = '`' + '\n'.join(keep) + '`'
   bot.send_message(chat_id=chatID, text=top,
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


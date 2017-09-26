#!/usr/bin/env python

# This script is based in the Adafruit Internet of Things Printer 2 and the Raspberry Pi email notifier.
# The script executes every X time a new email verification, it is something new it prints it. 
# Written by Adafruit Industries and modified by DAFR ELECTRONICS.  MIT license.
#
# MUST BE RUN AS ROOT (due to GPIO access)
#
# Required software includes Adafruit_Thermal, Python Imaging and PySerial
# libraries. Other libraries used are part of stock Python install.
#
# Original code can be found here:
#https://github.com/adafruit/Python-Thermal-Printer
#https://learn.adafruit.com/raspberry-pi-e-mail-notifier-using-leds/overview

#Not all of these are neccesary, but maybe helpful.
from Adafruit_Thermal import *
from neopixel import *
import RPi.GPIO as GPIO
from imapclient import IMAPClient
import gfx.logo2b as logo2b
import time
import subprocess
import quopri
import string
import re
import sys
from colors import *

# LED strip configuration:
LED_COUNT      = 1      # Number of LED pixels.
LED_PIN        = 18      # GPIO pin connected to the pixels (18 uses PWM!).
#LED_PIN        = 10      # GPIO pin connected to the pixels (10 uses SPI /dev/spidev0.0).
LED_FREQ_HZ    = 800000  # LED signal frequency in hertz (usually 800khz)
LED_DMA        = 5       # DMA channel to use for generating signal (try 5)
LED_BRIGHTNESS = 255     # Set to 0 for darkest and 255 for brightest
LED_INVERT     = False   # True to invert the signal (when using NPN transistor level shift)
LED_CHANNEL    = 0       # set to '1' for GPIOs 13, 19, 41, 45 or 53
LED_STRIP      = ws.WS2811_STRIP_GRB   # Strip type and colour ordering

# Create NeoPixel object with appropriate configuration.
strip = Adafruit_NeoPixel(LED_COUNT, LED_PIN, LED_FREQ_HZ, LED_DMA, LED_INVERT, LED_BRIGHTNESS, LED_CHANNEL, LED_STRIP)

#Create thermal printer object and load default configuration.
printer = Adafruit_Thermal("/dev/serial0", 19200, timeout=5)

# This function deletes or changes the parts of the email that we dont want. Uses the strings above. 
def decode_email(msg_str):
    body = quopri.decodestring(msg_str) #decodes
    body = body[body.find("Felicitaciones!"):] #start message to process from here...
    body = body[:body.rfind("Content-Type: multipart/related;")] #end message to process from here...
    cleanr = re.compile('<.*?>')
    body = re.sub(cleanr, '', body)
    body = string.replace(body,'\\n', ' ')
    body = string.replace(body,'\\r', ' ')
    body = string.replace(body,'=', ' ')
    body.lstrip()
    body.rstrip()
    body = body[:body.rfind("--_")] #a litle bit of timming
    body = re.sub('\s{2,}', ' ', body) #deletes double or more white spaces and left it as one space.
    body = unicode(str(body), 'utf-8') #character decodification
    decoded_message = body
    return decoded_message

#This function generates and prints our ticket based in the received info. (not used in the instructables example, but feel free to modify it) 
def ticket_summary (body2):
    pos = body2.find('PEDIDO: ') #search for a keyword
    ordernum = body2[pos + 8:pos +17] #and extracts the info next to it. Of course we know what we are searching for ;)
    pos1 = body2.find('TOTAL PAGADO ') 
    pos2 = body2.find('.', pos1)
    ordertotal = body2[pos1:pos2 + 3]
    ordernum.lstrip()
    ordernum.rstrip()
    ordernum.replace(" ", "")
    if DEBUG:
        print(' ')
        sys.stdout.write(BLUE)
        print('Numero de pedido: %s' %ordernum)
        print(ordertotal) 
        sys.stdout.write(RESET)
    printer.wake()
    printer.setDefault()
    printer.justify('C') #now the ticket is being printed
    printer.println("--------------------------------")
    printer.feed(1)
    printer.printBitmap(logo2b.width, logo2b.height, logo2b.data)
    printer.feed(1)
    printer.inverseOn()
    printer.println("  Ticket de pedido web  ")
    printer.inverseOff()
    printer.feed(1)
    printer.println("================================")
    printer.justify('L')
    printer.println("Consulta el detalle de tu pedido")
    printer.println("ingresando a tu cuenta en linea.")
    printer.println("Obten tu nota en formato PDF.   ")
    printer.println("================================")
    printer.justify('R')
    printer.underlineOn()
    printer.println(str(ordertotal))
    printer.underlineOff()
    printer.feed(1)
    printer.justify('L')
    printer.println("Numero de pedido: ")
    printer.printBarcode(str(ordernum),printer.CODE93)
    printer.justify('C')
    printer.boldOn()
    printer.println("GRACIAS POR TU COMPRA!")
    printer.boldOff()
    printer.println("www.2brobots.com")
    printer.feed(1)
    printer.println("------ REV:2A07012015DAFR ------")
    printer.feed(3)
    return

# Called when button is briefly tapped.  Invokes time/temperature script.
def tap():
  loop() #checks our inbox
  return

# Called when button is held down.  Prints image, invokes shutdown process.
def hold():
  subprocess.call("sync")
  subprocess.call(["shutdown", "-h", "now"]) #shutdowns the raspberry pi
  strip.setPixelColorRGB(0,0,0,0) #turn off the neopixel
  strip.show()
  printer.sleep()
  GPIO.cleanup()
  while True:
      time.sleep(1)
  return

#Program start here:
strip.begin()
strip.setPixelColorRGB(0,0,255,0) #booting script state, green color is showed in the neopixel.
strip.show()

 
DEBUG = False  #Change it to False when you are done debugging

# Here you can enter your email login details. 
HOSTNAME = 'imap.gmail.com'
USERNAME = 'yourmail@gmail.com'
PASSWORD = 'Password'
MAILBOX = 'MAILBOX'
 
NEWMAIL_OFFSET = 0   # only executes printing after the emails reach the minimun for processing.
MAIL_CHECK_FREQ = 60 # check mail every 60 seconds, you can change it.
 
GPIO.setwarnings(False)
GPIO.setmode(GPIO.BCM)

buttonPin    = 23

GPIO.setup(buttonPin, GPIO.IN, pull_up_down=GPIO.PUD_UP)

prevButtonState = GPIO.input(buttonPin)
prevTime        = time.time()
tapEnable       = False
holdEnable      = False
tapTime      = 0.01  # Debounce time for button taps
nextInterval = 0.0   # Time of next recurring operation
holdTime     = 10     # Duration for button hold (shutdown)

counter = 0

time.sleep(10)
 
def loop():
  try:  
    server = IMAPClient(HOSTNAME, use_uid=True, ssl=True)
    server.login(USERNAME, PASSWORD)
    
    select_info = server.select_folder(MAILBOX) 

    if DEBUG:
        print('Logging in as ' + USERNAME)
        print('%d messages in "Pedidos DAFR"' % select_info['EXISTS'])
 
    folder_status = server.folder_status(MAILBOX, 'UNSEEN')
    newmails = int(folder_status['UNSEEN'])
 
    if DEBUG:
        print "You have", newmails, "new recent emails!"


    messages = server.search(['UNSEEN']) #NOT DELETED to see all email available 

    if DEBUG:
        print("There are %d messages that aren't read" % len(messages))  
        print("Messages:")

    response = server.fetch(messages, ['FLAGS', 'RFC822.SIZE'])
    mail_array = []
    
    for msgid, data in response.iteritems():
        if DEBUG:
            print('   ID %d: %d bytes, flags=%s' % (msgid, data[b'RFC822.SIZE'], data[b'FLAGS']))    
        mail_array.append(msgid)
       
    
    if newmails > NEWMAIL_OFFSET:
        strip.setPixelColorRGB(0,0,0,255) #turn blue our neopixel if we have something to print
        strip.show()

        printer.wake()    
        time.sleep(5)
        printer.feed(1)

        for elements in mail_array:
            if printer.hasPaper() == True: #verify is printer has paper before printing.
               body = server.fetch(elements,['BODY.PEEK[TEXT]']) #IMPORTANT you might have problems with these, try using "TEXT", "1", "1.1", "1.2" or "2". 
               body2 = decode_email(str(body))
               if DEBUG:
                  sys.stdout.write(RED)
                  print(body) #prints in console original text.
                  print(' ')
                  sys.stdout.write(GREEN)
                  print(body2) #prints in console procesed text.
                  sys.stdout.write(RESET)
               ticket_summary(body2) #call the ticket printing routine
               time.sleep(5)
               if printer.hasPaper() == True: #verify is printer has paper after printing.
                  server.add_flags(elements, '\\Seen')  #mark as read if printed sucesfully.
               else:
                  strip.setPixelColorRGB(0,255,255,0) #show yellow neopixel if there is no paper in the printer.
                  strip.show()
                  if DEBUG:
                     print 'There is no paper in the printer.'
               if DEBUG:
                  print(' ')
                  time.sleep(5)
            else:
              strip.setPixelColorRGB(0,255,255,0) #show yellow neopixel if there is no paper in the printer.
              strip.show()
              if DEBUG:
                 print 'There is no paper in the printer.'
        printer.sleep() 
        
    else:
        strip.setPixelColorRGB(0,255,0,0) #show red neopixel if there are no emails for printing.
        strip.show()
        
  except:
    strip.setPixelColorRGB(0,255,0,255) #show purple neopixel if an error occurs reading the email.
    strip.show()
    if DEBUG:
        print 'Cant check email or an error has ocurred. Verify your internet conection or this script parameters'
 
    
 
if __name__ == '__main__':
    try:
        if DEBUG:
            print 'Press ctrl + c to quit'
        printer.wake()
        printer.sleep()
        strip.setPixelColorRGB(0,255,255,255) #show white neopixel while starting up. 
        strip.show()
        time.sleep(5)
        loop()
                    
        while True:
           time.sleep(1)
           # Poll current button state and time
           buttonState = GPIO.input(buttonPin)
           t           = time.time()
           # Has button state changed?
           if buttonState != prevButtonState:
              prevButtonState = buttonState   # Yes, save new state/time
              prevTime        = t
           else:                             # Button state unchanged
            if (t - prevTime) >= holdTime:  # Button held more than 'holdTime'?
              # Yes it has.  Is the hold action as-yet untriggered?
               if holdEnable == True:        # Yep!
                  hold()                      # Perform hold action (usu. shutdown)
                  holdEnable = False          # 1 shot...don't repeat hold action
                  tapEnable  = False          # Don't do tap action on release
            elif (t - prevTime) >= tapTime: # Not holdTime.  tapTime elapsed?
             # Yes.  Debounced press or release...
               if buttonState == True:       # Button released?
                 if tapEnable == True:       # Ignore if prior hold()
                    tap()                     # Tap triggered (button released)
                    tapEnable  = False        # Disable tap and hold
                    holdEnable = False
               else:                         # Button pressed
                 tapEnable  = True           # Enable tap and hold actions
                 holdEnable = True
           if counter >= MAIL_CHECK_FREQ:   
              loop()
              counter = 0
           else:
              counter = counter + 1
               
    finally:
        GPIO.cleanup() #reset the gpio pins functions.
        strip.setPixelColorRGB(0,0,0,0) #turn off neopixel at exit of this script. (shutting down or ctrl + c)
        strip.show()
        printer.sleep()

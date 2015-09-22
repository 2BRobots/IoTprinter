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
from imapclient import IMAPClient
import time
import RPi.GPIO as GPIO
from Adafruit_Thermal import *
from neopixel import *
import Image
import subprocess
import quopri
import string
import re

#This section is used to define what is going to be delated or changed, feel free to modify it.
cadena1 = '<td style="padding:0.6em 0.4em;">' 
cadena2 = "<br />"
cadena3 = "</td>"
cadena4 = "="
cadena5 = '<strong><a href"http://dafrelectronics.com/tienda/'
cadena6 = "</a>"
cadena7 = "</strong>"
cadena8 = '<td style"padding:0.6em 0.4em; text-align:right;">'
cadena9 = '<td style"padding:0.6em 0.4em; text-align:right;">'
cadena10 = '<td style"padding:0.6em 0.4em; text-align:center;">'
cadena11 = '<td style"padding:0.6em 0.4em; text-align:right;">'
cadena12 = "</tr>"
cadena13 = '\\t'
cadena14 = '\\r'
cadena15 = '\\n'
cadena16 = 'PRODUCTO  PRECIO UNITARIO  CANTIDAD  PRECIO TOTAL'
cadena17 = '<span style"color:; font-weight:bold;'
cadena18 = '</span>'
cadena19 = '<tr style"background-color:'
cadena20 = 'EBECEE;">'
cadena21 = '<br />'
cadena22 = '">' #'html">'
cadena23 = '$ '
cadena24 = '<br  />'
cadena25 = '<span  style"color:; font-weight:bold;">'
cadena26 = '. '
cadena27 = 'DDE2E6;">'
cadena28 = '<span style"color:; font-weight:bold;">'
cadena29 = 'e :'
cadena30 = '<span style"color:; font-weight:bold; '

# This function deletes or changes the parts of the email that we dont want. Uses the strings above. 
def decode_email(msg_str):
    body = quopri.decodestring(msg_str) #decodes
    body = body[187:] #start from character number...
    body = body[:-131] #end in character number...
    body = string.replace(body,cadena1, '')
    body = string.replace(body,cadena2, ' ')
    body = string.replace(body,cadena3, ' ')
    body = string.replace(body,cadena4, '')
    body = string.replace(body,cadena5, ' ')
    body = string.replace(body,cadena6, ' ')
    body = string.replace(body,cadena7, ' ')
    body = string.replace(body,cadena8, '')
    body = string.replace(body,cadena9, '')
    body = string.replace(body,cadena10, ' ')
    body = string.replace(body,cadena11, '')
    body = string.replace(body,cadena12, '')
    body = string.replace(body,cadena13, '')
    body = string.replace(body,cadena14, '')
    body = string.replace(body,cadena15, ' ')
    body = string.replace(body,cadena16, '')
    body = string.replace(body,cadena17, ' ')
    body = string.replace(body,cadena18, ' ')
    body = string.replace(body,cadena19, '')
    body = string.replace(body,cadena20, ' ')
    body = string.replace(body,cadena21, ' ')
    body = string.replace(body,cadena22, ' ')
    body = string.replace(body,cadena23, '$')
    body = string.replace(body,cadena24, ' ')
    body = string.replace(body,cadena25, ' ')
    body = re.sub('\s{2,}', ' ', body) #deletes double or more white spaces and left it as one space.
    body = string.replace(body,cadena26, '.')
    body = string.replace(body,cadena27, '')
    body = string.replace(body,cadena28, '')
    body = string.replace(body,cadena29, 'e:')
    body = string.replace(body,cadena30, ' ')
    body = re.sub('\s{2,}', ' ', body) #deletes double or more white spaces and left it as one space.
    body = unicode(str(body), 'utf-8') #character decodification
    msg = body
    decoded_message = msg
    return decoded_message

#This function generates and prints our ticket based in the received info. (not used in the instructables example, but feel free to modify it) 
def ticket_summary (body2):
    pos = body2.find('PEDIDO: ') #search for a keyword
    ordernum = body2[pos + 8:pos +17] #and extracts the info next to it. Of course we know what we are searching for ;)
    pos1 = body2.find('TOTAL PAGADO ') 
    pos2 = body2.find('.', pos1)
    ordertotal = body2[pos1:pos2 + 3]
    printer.justify('L') #now the ticket is being printed
    printer.println("--------------------------------")
    printer.feed(2)
    printer.printImage(Image.open('dafr webpage mono.bmp'),True)
    printer.println("Todo el material pra tu proyecto")
    printer.feed(1)
    printer.println("================================")
    #printer.println("  ID  CANTIDAD  PRECIO  SUBTOTAL")
    printer.println("Consulta el detalle de tu pedido")
    printer.println("ingresando a tu cuenta en linea.")
    printer.println("Obten tu nota en formato PDF.   ")
    printer.println("================================")
    #printer.println("              DESCUENTO:  $20.00")
    #printer.println("--------------------------------")
    printer.println(ordertotal)
    printer.feed(1)
    printer.println("Numero de pedido: ")
    printer.printBarcode(ordernum,printer.CODE93)
    printer.justify('C')
    printer.println("GRACIAS POR TU COMPRA!")
    printer.println("www.dafrelectronics.com")
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
  return


# LED strip configuration:
LED_COUNT      = 1       # Number of LED pixels.
LED_PIN        = 18      # GPIO pin connected to the pixels (must support PWM!).
LED_FREQ_HZ    = 800000  # LED signal frequency in hertz (usually 800khz)
LED_DMA        = 5       # DMA channel to use for generating signal (try 5)
LED_BRIGHTNESS = 255     # Set to 0 for darkest and 255 for brightest
LED_INVERT     = False   # True to invert the signal (when using NPN transistor level shift)


# Create NeoPixel object with appropriate configuration.
strip = Adafruit_NeoPixel(LED_COUNT, LED_PIN, LED_FREQ_HZ, LED_DMA, LED_INVERT)
# Intialize the library (must be called once before other functions).
strip.begin()

#Create thermal printer object and load default configuration.
printer = Adafruit_Thermal("/dev/ttyAMA0", 19200, timeout=5)

#Program start here:
strip.setPixelColorRGB(0,0,255,0) #booting script state, green color is showed in the neopixel.
strip.show()

 
DEBUG = True  #Change it to False when you are done debugging

# Here you can enter your email login details. 
HOSTNAME = 'imap.gmail.com'
USERNAME = 'youraccount@gmail.com'
PASSWORD = 'accountpassword'
MAILBOX = 'Secret messages'
 
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
        print('%d messages in "Secret messages"' % select_info['EXISTS'])
 
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
    
    if DEBUG:
       for elements  in mail_array:
           print(elements)
       

    
    if newmails > NEWMAIL_OFFSET:
        strip.setPixelColorRGB(0,0,0,255) #turn blue our neopixel if we have something to print
        strip.show()


        printer.wake()    
        time.sleep(5)
        printer.feed(1)

        for elements in mail_array:
            if printer.hasPaper() == True: #verify is printer has paper before printing.
               body = server.fetch(elements,['BODY.PEEK[1]']) #IMPORTANT you might have problems with these, try using "1", "1.1", "1.2" or "2". 
               if DEBUG:
                  print(body) #prints in console original text.
                  print(' ')
               body2 = decode_email(str(body)) #process the received text.
               if DEBUG:
                  print (body2) #prints in console processed text.
               #ticket_summary(body2) #call the ticket printing routine
               printer.println(body) #prints in paper the original text of the email. Change to "body2" for printing the processed version.
               if printer.hasPaper() == True: #verify is printer has paper after printing.
                  server.add_flags(elements, '\\Seen')  #mark as read if printed sucesfully.
               else:
                  strip.setPixelColorRGB(0,255,255,0) #show yellow neopixel if there is no paper in the printer.
                  strip.show()
                  if DEBUG:
                     print 'There is no paper in the printer.'
               if DEBUG:
                  print(' ')
                  time.sleep(12)
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




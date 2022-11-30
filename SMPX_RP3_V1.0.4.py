# File:        SMPX_RP3_V1.0.4.ino
# Description: Program to handle serial switching from Auto Pilot / GCS to Two (2) radios , Silvius and 
#              Microhard. Program would send and receive heartbeat messagges, to determine the Link Status.
#              Program would prioritize Silvus link over MicroHard, so everytime that Silvus link is available
#              it will become the priority link for Data Transmission
#              ----------------------------------------------------------------------------------------------
# Notes      : Major, Minor and Revision notes:
#              ----------------------------------------------------------------------------------------------
#              Major    - Software major number will counting up each time there is a major changes on the
#                         software features. Minor number will reset to '0' and revision number will reset
#                         to '1' (on each major changes). Initially major number will be set to '1'
#              Minor    - Software minor number will counting up each time there is a minor changes on the
#                         software. Revision number will reset to '1' (on each minor changes).
#              Revision - Software revision number will counting up each time there is a bug fixing on the
#                         on the current major and minor number.
#              ----------------------------------------------------------------------------------------------
#              Current Features & Bug Fixing Information
#              ----------------------------------------------------------------------------------------------
#               0001 - (22.nov.22) - re-arrange the structure of the codes, putting critical function on top 
#                                    of other functions to prioritize it. Improves the process speed
#               0002 - (22.nov.22) - replaced ser.readline() to ser.read(x), doing this improves drastically
#                                    the smoothness of reading GCS and Autipilot data. Changing to 
#                                    ser.read(ser.in_waiting) improves the speed even more
#               0003 - (22.nov.22) - delete line that put ser.read(ser.in_waiting) into variable, instead just
#                                    directly put it into ser.write(ser.read(ser.in_waiting)) to remove 
#                                    unnecessary variables and process
#               0004 - (23.nov.22) - remove AIR and GROUND structure, now program has only 1 mode. Send and
#                                    return values of HeartBeat are the same
#               0005 - (23.nov.22) - create def changeHeartBeat, and trigger this function as a thread, to put
#                                    make processRxMessage function takes less time
#               0006 - (23.nov.22) - change PRIMARYLINK and SECONDARYLINK from integer values 1 & 2, to String 
#                                    '1' and '2'. Reason because passing an int to a thread argument is not
#                                    permissable for non iterable objects.
#               0007 - (24.nov.22) - remove thread on function checkHeartBeat, inititate function by only
#                                    calling it in processRxMessage()
#               0008 - (24.nov.22) - fix bug message.strip(b'/xfe/x0b/xfe') to message.strip(commsHeartBeatMessage)
#               0009 - (24.nov.22) - add condition, if message != b'' after stripping the commsheartbeat, then
#                                    ignore message and DONT send to GCS / Autopilot
#               0010 - (24.nov.22) - added  print(f'Sent HeartBeat Message = {commsHeartBeatMessage}') line to 
#                                    statusPrint()
#               0011 - (24.nov.22) - added serial initialization condition on serialEvent() for ser1.write()
#                                    and ser2.write()
#               0012 - (24.nov.22) - put ser.read(ser.in_waiting) in variable 'message'. Have issues in using it
#                                    if not put in a variable. Effected functions serialEvent(), serialEvent1()
#                                    and serialEvent2()
#               0013 - (30.nov.22) - define serial port based on virtual port refference to specified product id
#                                    and vendor id. Change from initializing as /dev/ttyUSB0 to /dev/MainComm,
#                                    /dev/ttyUSB1 to /dev/SilvusComm and /dev/ttyUSB2 to /dev/MicroHardComm
#              ----------------------------------------------------------------------------------------------
# 
# Author          : Mohd Danial Hariz Bin Norazam (393), Sabri Bin Azman (431)
# Supervisor      : Ahmad Bahari Nizam B. Abu Bakar.
# Current Version : Version 1.0.4
# 
# -------------------------------------------------------------------------------------------------------------
#                                           History Version
# -------------------------------------------------------------------------------------------------------------
# Version - 1.0.1 = (0001,0002,0003)
# Version - 1.0.2 = (0004,0005,0006)
# Version - 1.0.3 = (0007,0008,0009,0010,0011,0012)
# Version - 1.0.4 = (0013)

import serial
import time
from threading import Thread

PRIMARYLINK = '1' # silvius link
SECONDARYLINK = '2' # uAvionics link

primaryLinkStatus = True # this is the link status for Silvius Radio Link
secondaryLinkStatus = True # this is the link status for uAvionics Radio Link
priorityLink = PRIMARYLINK # which link is the c2 prioritizing

timeOutCounter = 0
timeOutCounter1 = 0
emitcounter = 0

commsHeartBeatStatus = False
commsHeartBeatMessage = bytes([0xFE]) + bytes([0x0B]) + bytes([0xFE]) # This is the hearbeat message

# create global variable for Serial0 
serialInitStatus = False
ser = None

# create global variable for Serial1
serialInitStatus1 = False
ser1 = None

# create global variable for Serial2
serialInitStatus2 = False
ser2 = None

# Serial event function, innitiate and listen to Serial0 - comms from / to autopilot
def serialEvent():
    global ser
    global serialInitStatus
    
    while not serialInitStatus :
        try:
            initSerial("Serial",'/dev/MainComm',57600,serial.PARITY_NONE,serial.STOPBITS_ONE,serial.EIGHTBITS,5)
            ser.reset_input_buffer()
            serialInitStatus = True
            break
        except Exception as e:
            print(f'Serial Init exception has occured: {e}')
            print("Retrying Connection")
            time.sleep(5)
        
    while serialInitStatus:    
        if ser.in_waiting > 0:
            message = ser.read(ser.in_waiting)
            # try:
            #     # message = ser.read(ser.in_waiting)
            #     # print(message)
            # except Exception as e:
            #     print(f'Decoding exception error at Serial 0 has occured: {e}')
            # print(ser.read(ser.in_waiting))
            if priorityLink == PRIMARYLINK and serialInitStatus1:
                    ser1.write(message)
            elif priorityLink == SECONDARYLINK and serialInitStatus2:
                    ser2.write(message)

#Serial 1 event function, innitiate and listen to Serial1 - comms from / to Silvius             
def serialEvent1():
    global ser1
    global serialInitStatus1
    
    while not serialInitStatus1 :
        try:
            initSerial("Serial1",'/dev/SilvusComm',57600,serial.PARITY_NONE,serial.STOPBITS_ONE,serial.EIGHTBITS,5)
            ser1.reset_input_buffer()
            serialInitStatus1 = True
            break
        except Exception as e:
            print(f'Serial 1 Init exception has occured: {e}')
            print("Retrying Connection")
            time.sleep(5)
        
    while serialInitStatus1:   
        if ser1.in_waiting > 0:
            message = ser1.read(ser1.in_waiting)
            try:
                processRxMessage(message,PRIMARYLINK)
                # ser1.read(ser1.in_waiting)
                # print(f'This is a received message from Silvus = {message}') 
                # ser.write(ser1.read(ser1.in_waiting))
            except Exception as e:
                print(f'Decoding exception error at Serial 1 has occured: {e}')
            # processRxMessage(ser1.read(ser1.in_waiting),PRIMARYLINK)
 
#Serial 2 event function, innitiate and listen to Serial2 - comms from / to uAvionics                    
def serialEvent2():
    global ser2
    global serialInitStatus2
    
    while not serialInitStatus2 :
        try:
            initSerial("Serial2",'/dev/MicroHardComm',57600,serial.PARITY_NONE,serial.STOPBITS_ONE,serial.EIGHTBITS,1)
            ser2.reset_input_buffer()
            serialInitStatus2 = True
            break
        except Exception as e:
            print(f'Serial 2 Init exception has occured: {e}')
            print("Retrying Connection")
            time.sleep(5)
            
    while serialInitStatus2:  
        if ser2.in_waiting > 0:
            message = ser2.read(ser2.in_waiting)
            # print(ser2.read(ser2.in_waiting))
            try:
                # print(f'This is a received message from microHard = {message}') 
                processRxMessage(message,SECONDARYLINK)
                # message = ser2.readline()
            except Exception as e:
                print(f'Decoding exception error at Serial 2 has occured: {e}')
                    
# Function to process the retrieved message and see if the message contains heartbeat.
# If heartbeat is contained in message, reset the timeoutcounter based on which link the message was received from                  
def processRxMessage(message,rxMessageLink):
    global commsHeartBeatStatus  
    # print(message)
    if commsHeartBeatMessage in message:
        # print(f'received heartbeat = {message} compared with = {commsHeartBeatMessage}')
        commsHeartBeatStatus = True
        # print(commsHeartBeatMessage)
        checkHearBeat(rxMessageLink)
        message = message.strip(commsHeartBeatMessage)
        
    if message != b'':
        ser.write(message)
        # print(message)
        # print(rxMessageLink)
        # print('sent to Autopilot')
        # Thread(target =checkHearBeat, args = (rxMessageLink)).start()

def checkHearBeat(rxMessageLink):
    global commsHeartBeatStatus  
    global timeOutCounter
    global timeOutCounter1
    global primaryLinkStatus
    global secondaryLinkStatus
    
    # print('thread start')
    if commsHeartBeatStatus:                        # if the received heartbeat flag is true
        if rxMessageLink == PRIMARYLINK:            # if the received message is from PRIMARYLINK (silvus)
            # print('reset counter')
            timeOutCounter = 0                      # reset the timeoutcounter for PRIMARYLINK
            primaryLinkStatus = True                # set the primary link status flag to true
        
        if rxMessageLink == SECONDARYLINK:        # else if the received message is from SECONDARYLINK (uAvionics)
            timeOutCounter1 = 0                     # reset the timeoutcounter1 for SECONDARYLINK
            secondaryLinkStatus = True              # set the secondary link status flag to true

    commsHeartBeatStatus = False                         # reset flag to false
    
def linkStatus():
    global timeOutCounter
    global timeOutCounter1
    global primaryLinkStatus
    global secondaryLinkStatus
    global priorityLink
    
    while True:
        time.sleep(.1) # delay for 100ms
        
        # check if primary link still up
        if primaryLinkStatus:                                   # when the primary link status is true, start counting
            #print("PrimaryLinkStatus is True")
            if timeOutCounter >= 100:                            # if the counter reaches 100 (equavalent to 10 seconds)
                print("Primary Link was Lost for 10 Seconds")
                primaryLinkStatus = False                       # set primarylinkstatus flag to false
            else: 
                timeOutCounter +=1                              # if counter is not yet 100, count up
        
        if secondaryLinkStatus:                                 # when the secondary link status is true, start counting
            # print("SecondaryLinkStatus is True")
            if timeOutCounter1 >= 100:                           # if the counter reaches 100 (equavalent to 10 seconds)
                print("Secondary Link was Lost for 10 Seconds")
                secondaryLinkStatus = False                     # set secondarylinkstatus flag to false
            else: 
                timeOutCounter1 +=1                             # if counter is not yet 100, count up 
        
        if primaryLinkStatus:
            priorityLink = PRIMARYLINK
        elif not primaryLinkStatus and secondaryLinkStatus:
            priorityLink = SECONDARYLINK
            
        # priorityLink = PRIMARYLINK
        # time.sleep(10)
        # priorityLink = SECONDARYLINK
        # time.sleep(10)

# Emit heart beat function for every 2 seconds
def emitHeartbeat():
    global emitcounter
    
    while True:
        time.sleep(0.1)
        if emitcounter >= 20:
            message = commsHeartBeatMessage
            # print(message)
            if serialInitStatus1:
                ser1.write(message)
                # print(message)
            if serialInitStatus2:
                ser2.write(message)
            emitcounter = 0
        else:
            emitcounter +=1
                
def initSerial(DeviceName,Port,Baudrate,Parity,Stopbits,Bytesize,Timeout):
    global ser
    global ser1
    global ser2
    
    if DeviceName == "Serial":
        ser = serial.Serial(            
            port=Port,
            baudrate = Baudrate,
            parity=Parity,
            stopbits=Stopbits,
            bytesize=Bytesize,
            timeout=Timeout
            )
    if DeviceName == "Serial1":
        ser1 = serial.Serial(            
            port=Port,
            baudrate = Baudrate,
            parity=Parity,
            stopbits=Stopbits,
            bytesize=Bytesize,
            timeout=Timeout
            )
    if DeviceName == "Serial2":
        ser2 = serial.Serial(            
            port=Port,
            baudrate = Baudrate,
            parity=Parity,
            stopbits=Stopbits,
            bytesize=Bytesize,
            timeout=Timeout
            )
        
def statusPrint():
    while True:
        print('************************************************')
        print(f'Sent HeartBeat Message = {commsHeartBeatMessage}')
        print(f'Priority Link is = {priorityLink}')
        print(f'Primary Link Status = {primaryLinkStatus}')
        print(f'Secondary Link Status = {secondaryLinkStatus}')
        print(f'Primary Link Timeout = {timeOutCounter / 10}s')
        print(f'Secondary Link Timeout = {timeOutCounter1 / 10}s')
        print("")
        time.sleep(2)
        

if __name__ == '__main__':
    Thread(target=serialEvent).start()
    Thread(target=serialEvent1).start()
    Thread(target=serialEvent2).start()
    Thread(target=linkStatus).start()
    Thread(target=emitHeartbeat).start()
    Thread(target=statusPrint).start()


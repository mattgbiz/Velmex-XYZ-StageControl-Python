### XYZ Stage from Velmex Controlled by VXM Controller ###
"""
**********************************************************
*     Developed By: Ohio State University NARS Lab       *
*                 Developer: Matt Bisbee                 *
*               Very Early Version of code               * 
**********************************************************
"""

from serial import Serial
import time
#port is from my computer and baud rate is from his specs
port = 'COM4'
baud = 9600
maxWaitTime = 0.1 #this is in seconds and I will play around with it
#XYZ = serial.Serial(port='COM4',baudrate=9600,timeout=5)

#get some constants/defaults
defaultVelocity = 2000
stepsTomm = 0.0050
mmToSteps = (1/0.0050)
mmToin = (1/25.4)
inTomm = 25.4


#Make a Class for the VXM Stage
class VXM(object):
    #initialize our stage
    def __init__(self, port, baud, maxWaitTime):
        self._port = Serial(port=port,baudrate=baud,timeout=maxWaitTime)
        print('Initializing Stage on port: %s' %(port))
        #set default motor speeds: The manual says 2000 steps/second is good
        self.setVelocity('X',defaultVelocity)
        self.setVelocity('Y',defaultVelocity)
        self.setVelocity('Z',defaultVelocity)

    def home(self):
        #Move all of the stages to 0
        self.moveToZero('X')
        time.sleep(1)
        self.moveToZero('Y')
        time.sleep(1)
        self.moveToZero('Z')
        self.getAllPositions()


    #provide function for sending commands
    def sendcmd(self, commandString, silent=True):
        #add the return variable \r and convert to bytes
        stringToSend = (commandString + '\r').encode()
        #flush the input buffer
        self._port.flushInput()
        self._port.write(stringToSend)
        if silent == False:
            print('Sent Stage Command: %s' %(commandString))

    #Function for getting response from stage
    def getresp(self, silent=True):
        resp = self._port.readline().decode() #the decode makes it be a string not a byte string aka 'string' not b'string'
        if silent == False:
            print(resp)
        #flush the output buffer
        self._port.flushOutput()    
        return resp  

    def waitReady(self, silent=False):
        #I want this command to go into all moves and things that take time
        #When one sends V to the stage, it returns B if busy, R if ready, J if in jog/slew mode, b if Jog/Slewing
        #need to wait for it to return R
        status = 'S'        #calling it S for start
        while status != 'R':
            if silent == True:
                print('Sending command V')
            self.sendcmd('V')
            #now get a response
            status=self.getresp()
            if silent == True:
                print('Got a response: %s' %(status))
            time.sleep(0.1) #sleep for a tenth of a second
        
            
    
    #Function to get individual stage position
    def getPosition(self, Stage, metric_units=True, english_units=False):
        assert Stage == 'X' or Stage == 'Y' or Stage == 'Z'
        self.sendcmd(Stage)
        stageResp = str(self.getresp())
        #pull the number out of string
        stageNum = int(stageResp[2:9])    #turns the string of 7 digits into an integer  
        if stageResp[1] == '-':          #see if second value is + or -
            stageNum = stageNum*(-1)      #if negative, make it a negative value
        #Convert from steps to mm 0.0050 is in manual
        stagemm = float(stepsTomm*stageNum)
        stagein = stagemm/25.4 
        #print it out
        #by default, metric units is true, so if we want english units to be displayed, specifcy english_units = True in the function call
        if english_units == True:
            if Stage == 'X':
                print('X Position: %fin' %(stagein))
            elif Stage == 'Y':
                print('Y Position: %fin' %(stagein))
            elif Stage == 'Z':
                print('Z Position: %fin' %(stagein))
            return stagein        
        if metric_units == True:
            if Stage == 'X':
                print('X Position: %fmm' %(stagemm))
            elif Stage == 'Y':
                print('Y Position: %fmm' %(stagemm))
            elif Stage == 'Z':
                print('Z Position: %fmm' %(stagemm)) 
            return stagemm


    #Function to get the X,Y,Z positions at same time
    def getAllPositions(self, metric_units = True, english_units = False):
        self.sendcmd('X',silent=False)       #gets X position
        Xresp = str(self.getresp(silent=False))          
        self.sendcmd('Y',silent=False)       #get Y position
        Yresp = str(self.getresp(silent=False))
        self.sendcmd('Z',silent=False)       #get Z position   
        Zresp = str(self.getresp(silent=False))
        #get values from the strings
        #The first part of response is the axis, second is + or - and last 7 are the positions
        def getNumber(Axisresp):
            Axisnum = int(Axisresp[2:9])    #turns the string of 7 digits into an integer  
            if Axisresp[1] == '-':          #see if second value is + or -
                Axisnum = Axisnum*(-1)      #if negative, make it a negative value
            return Axisnum
        
        Xnum = getNumber(Xresp) #turns the string of 7 digits into an integer
        Ynum = getNumber(Yresp)
        Znum = getNumber(Zresp)
        #Conversions 1 step is 0.0050mm
        Xmm = float(stepsTomm*Xnum)           #make these values float since they were integers
        Ymm = float(stepsTomm*Ynum)
        Zmm = float(stepsTomm*Znum)
        #conversion 25.4 mm is 1 in
        Xin = Xmm/25.4
        Yin = Ymm/24.4
        Zin = Zmm/25.4
        #time.sleep(1)
        #print('Stage Positions- {} {} {}'.format(Xresp,Yresp,Zresp)) #it doesnt like this print for some reason
        #by default, metric units is true, so if we want english units to be displayed, specifcy english_units = True in the function call
        if english_units == True:
            print('Stage Positions: X=%fin Y=%fin Z=%fin' %(Xin,Yin,Zin))
            return Xin, Yin, Zin
        if metric_units == True:
            print('Stage Positions: X=%fmm Y=%fmm Z=%fmm' %(Xmm,Ymm,Zmm))
            return Xmm, Ymm, Zmm

    def setVelocity(self, Stage, Speed):
        #make sure someone is only trying to input velocity for one of the 3 axes
        assert Stage == 'X' or Stage == 'Y' or Stage == 'Z'
        assert Speed > 0 and Speed <= 6000 #the motor speed must be in range 1-6000  
        if Stage == 'X':
            Velocity = 'E,C,S1M' + str(Speed) + ',R'
            self.sendcmd(Velocity)
            print('Velocity of Stage %s set to %s' %(Stage,Speed))
        elif Stage == 'Y':
            Velocity = 'E,C,S2M' + str(Speed) + ',R'
            self.sendcmd(Velocity)
            print('Velocity of Stage %s set to %s' %(Stage,Speed))
        elif Stage == 'Z':
            Velocity = 'E,C,S3M' + str(Speed) + ',R'
            self.sendcmd(Velocity)
            print('Velocity of Stage %s set to %s' %(Stage,Speed))
        else:
            print('Did not set a speed to a stage') 
            
    def moveToZero(self,Stage):
        assert Stage == 'X' or Stage == 'Y' or Stage == 'Z'
        #make the command to move to zero
        if Stage == 'X':
            Zero = 'E,C,IA1M0,R'
        elif Stage == 'Y':
            Zero = 'E,C,IA2M0,R'
        elif Stage == 'Z':
            Zero = 'E,C,IA3M0,R'
        self.sendcmd(Zero)
        #now we have sent the command to move the stage back to zero
        #need to wait for the stage to finish getting to zero
        self.waitReady()
    
    def move_mm(self,Stage,dist_mm):
        assert Stage == 'X' or Stage == 'Y' or Stage == 'Z'
        #get the distance in mm to be in steps not mm
        dist_step = dist_mm*mmToSteps
        #make the command to move the stage
        if Stage == 'X':
            movemm = 'E,C,I1M' + str(dist_step) +',R'
        elif Stage == 'Y':
            movemm = 'E,C,I2M' + str(dist_step) +',R'
        elif Stage == 'Z':
            movemm = 'E,C,I3M' + str(dist_step) +',R'
        self.sendcmd(movemm)
        #now we have sent the command to move the stage back to zero
        #need to wait for the stage to finish getting to zero
        self.waitReady()
    
    def move_in(self,Stage,dist_in):
        assert Stage == 'X' or Stage == 'Y' or Stage == 'Z'
        #get the distance in mm to be in steps not mm
        dist_step = dist_in*inTomm*mmToSteps
        #make the command to move the stage
        if Stage == 'X':
            movein = 'E,C,I1M' + str(dist_step) +',R'
        elif Stage == 'Y':
            movein = 'E,C,I2M' + str(dist_step) +',R'
        elif Stage == 'Z':
            movein = 'E,C,I3M' + str(dist_step) +',R'
        self.sendcmd(movein)
        #now we have sent the command to move the stage back to zero
        #need to wait for the stage to finish getting to zero
        self.waitReady()



    def __del__(self):
        self._port.close()



XYZ = VXM(port,baud,maxWaitTime)
#XYZ.getStatus()
XYZ.home()   
XYZ.move_in('X',1)
XYZ.getPosition('X',english_units=True)
XYZ.move_in('Y',2)
XYZ.getPosition('Y',english_units=True)
XYZ.move_in('Z',2.5)
XYZ.getPosition('Z',english_units=True)
XYZ.home()     
#XYZ.getAllPositions()
#XYZ.setVelocity('X',1500)
del XYZ
#XYZ.write('E,C,I3M400,R\r'.encode())
#I will need to make a waitStop function that basically waits for the VXM to return that it is ready, to get around the timeout function

"""
#I really hope I don't screw with this thing
command = 'E,V'
print(command)
newcommand = command.encode()
print(newcommand)
XYZ.write(newcommand)
print('below first write') #does this just somply do something
basic = 'E,C,I3M2000,R\r'.encode()
XYZ.write(basic)
#I tried XYZ.read_until(b'\r') but that didnt work
print(XYZ.readline()



#print(XYZ.readline())
print('we are after readline()')
talktome = 'Z\r\n'.encode()
XYZ.write(talktome)
print(XYZ.readline())
print('we are at end')
"""
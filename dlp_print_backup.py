import cv2
import numpy as np
import os,sys,stat
import time
import threading
import RPi.GPIO as GPIO
import serial

""" Print Class
    Gohome: go to the liquid

    Hail 409!
"""     

#################  2016.9.11  add pwm and gpio ##########3
GPIO.setmode(GPIO.BOARD)
GPIO.setup(16,GPIO.OUT)     # for gpio  relay
GPIO.output(16,GPIO.LOW)    #relay

GPIO.setup(12,GPIO.OUT)     # for pwm  steering
p_pwm = GPIO.PWM(12,50)
p_pwm.start(0)
p_pwm.ChangeDutyCycle(3.0)
time.sleep(2)
#GPIO.cleanup(12)
############### serial ############################3

ser = serial.Serial('/dev/ttyAMA0',9600,timeout=1)

print ser.isOpen()

acerPowerOn  = "* 0 IR 001\r"
acerPowerOff = "* 0 IR 002\r"

####################################################


Z_limit = 500    #150
Z_before = 0
Z_set    = 0
Z_layernow = 0
pitch = 4.0    #pitch 
class Print(threading.Thread):
    def __init__(self,dirname,exposure_time,height_in):
        threading.Thread.__init__(self)
        self.currentLayer = 0
        self.totalLayer = 0
        self.isfinishPrint = 0
        self.dirname = dirname
        self.height = float(height_in)   #HEIGHT
        stepper_init()
        #for stepper
        self.exposure_trans = exposure_time
        self.stepper_pullback = 5.0
        self.exposure_t = 0 #int(exposure_time*1000)
        self.stop = False
        self.suspend = False
         
    def run(self):
        """ Print step1 : PNG and Stepper Init
            Hail 409!
        """     
        global Z_before 
        global Z_set    
        global Z_layernow
        global Z_limit
        self.SteerPrintOff()              # do not let the light in!!
        png_inputdir = self.dirname       # a dir without '/' FROM user input!!
        height_float = self.height  
        
        stepper_pb = self.stepper_pullback #pull back each time
        """ Print step2 : Show and Move
            Hail 409!
        """
        self.isfinishPrint = 0    
        svg_num = 1
        back_ground = cv2.imread("/home/pi/1920-1080.png")
        blank_p = cv2.imread("/home/pi/1920-1080.png")
        
        ##........place to change the scale
        r_plus  = 1.0  

        Gohome()
        Z_set = 0
        Z_before = 0
        ################# start print Move ############################
        Z_layernow = height_float * svg_num
        Z_set = Z_layernow
        step_move()
        
        ################# start list  ################################
        Png_files = os.listdir(self.dirname)
        Png_files.sort()
      #  try:
           # os.system('rm ' + png_inputdir + '/Thumbs.db')
       #    print "haha"
       # except:
       #     pass
       # print self.exposure_trans
       #.......
        
        cv2.namedWindow("image",cv2.WINDOW_NORMAL)
        cv2.setWindowProperty("image",0,1)
        cv2.imshow("image",blank_p)
        ser.write(acerPowerOn)
        #cv2.waitKey(60000)
       #.......
        #self.SteerPrintOn()
        for Png_name in Png_files:
                if svg_num == 1:   #exposure time in first time is different
                    self.exposure_t = int(self.exposure_trans  *3)
                    #self.SteerPrintOn()
                else:
                    self.exposure_t = int(self.exposure_trans )
                    
                str1 = png_inputdir + "/"+ Png_name
        #        print "mm"
                img = cv2.imread(str1)
                #if(img.shape >= back_ground.shape):
                   # break
                # SHOW Image
                img_r = cv2.resize(img,None,fx=r_plus,fy=r_plus,interpolation=cv2.INTER_CUBIC)#resize
                
                cv2.imshow("image",img_r)
                cv2.waitKey(self.exposure_t)   # delay ms
                if svg_num == 1:
                    cv2.waitKey(200)
                    self.SteerPrintOn()
                    cv2.waitKey(self.exposure_t)
                # SHOW Black 
                cv2.imshow("image",blank_p)  #blank
                cv2.waitKey(1)  #delay 1000  ,easy to change
                # Move UP
                Z_set = Z_set + stepper_pb #+ height_float
                step_move()
                # Move DOWN
                while self.suspend is True and self.stop is False:
                    time.sleep(0.5)
                    #self.SteerPrintOff()    #steering down 
                if self.stop:
                    self.currentLayer = -2
                    ser.write(acerPowerOff)
                    self.MotorPrintOver()
                    self.SteerPrintOff()    #steering down 
                    break
                Z_layernow =  height_float * (svg_num + 1) #height_float * (svg_num + 1)
                Z_set = Z_layernow
                step_move()
                #...
                #return_key = cv2.waitKey(10)
                
                #print return_key
                #if return_key == 27:            ##press 'ESC' to exit
                #    break    
                #if return_key == 113:           ##press 'q ' to pause
                #    return_key_continue = cv2.waitKey(0)
                #    #raw_input("Waiting for g to continue")
                #    return_key = 0
                #    pass
                self.currentLayer = svg_num
                svg_num = svg_num + 1
                if svg_num == self.totalLayer:
                    ser.write(acerPowerOff)
                    self.SteerPrintOff()      # control the steering
                    self.MotorPrintOver()
                    self.currentLayer=-1
                    break
       
        
    def getcurrentLayer_print(self):
        return self.currentLayer

    def thread_suspend(self):
        if self.suspend:
            self.suspend = False
        else:
            self.suspend = True

    def getTotalLayer(self):
        #height
        dir_count = len( os.listdir(self.dirname) )
        self.totalLayer = dir_count
        return self.totalLayer
        
    def getTotalLayer2(self):
        png_inputdir = self.dirname       
        name_filesvglog = self.dirname + '/print.log'
        fn_svglog = open(name_filesvglog)
        height = fn_svglog.readline()       #trans into float
        height = height.strip('\n')
        height_float = float(height)
        total = fn_svglog.readline()        #trans into int
        total = total.strip('\n')
        total_int = int(total)
        self.totalLayer = total_int
        fn_svglog.close()
        return self.totalLayer
    
    def thread_stop(self):
        self.stop=True
                                         
    def MotorPrintOver(self):
	global Z_set
	global Z_limit
	global Z_before
        Z_set = Z_set + 50.0
        step_move_fast()
        
################ def pwm   ##############
    def SteerPrintOn(self):
        GPIO.setmode(GPIO.BOARD)
        GPIO.setup(12,GPIO.OUT)
        p_pwm = GPIO.PWM(12,50)
        p_pwm.start(0)
        p_pwm.ChangeDutyCycle(4.3)
        #GPIO.cleanup(12)
    
        GPIO.output(16,GPIO.HIGH)
        time.sleep(2)

    def SteerPrintOff(self):
        GPIO.setmode(GPIO.BOARD)
        GPIO.setup(12,GPIO.OUT)
        p_pwm = GPIO.PWM(12,50)
        p_pwm.start(0)
        p_pwm.ChangeDutyCycle(2.6)
        #GPIO.cleanup(12)
    
        GPIO.output(16,GPIO.LOW)
        time.sleep(2)


################ def Motor ###################

def stepper_init():
    GPIO.setmode(GPIO.BOARD)
    GPIO.setup(11,GPIO.OUT)     #pwm control
    GPIO.setup(13,GPIO.OUT)     #direct control 
    GPIO.setup(15,GPIO.IN)      #home singal

def MotorDOWN():         #close to the liquid
    GPIO.output(13 , GPIO.LOW)

def MotorUP():         #far from the liquid 
    GPIO.output(13 , GPIO.HIGH)

def step_control(distance):   #def for control step
    global pitch
    step_number = 6400 * distance / pitch
    count = 0;
    while (count < step_number):
        GPIO.output(11 , GPIO.HIGH)
        time.sleep(0.00005)
        GPIO.output(11 , GPIO.LOW)
        time.sleep(0.00005)
        #print "outputing "
        count = count + 1    

def step_control_fast(distance):   #def for control step
    global pitch
    step_number = 6400 * distance / pitch
    count = 0;
    while (count < step_number):
        GPIO.output(11 , GPIO.HIGH)
        time.sleep(0.00001)
        GPIO.output(11 , GPIO.LOW)
        time.sleep(0.00001)
        #print "outputing "
        count = count + 1    

def step_move():
    global Z_set
    global Z_before
    global Z_limit
    if Z_set > Z_limit:
        Z_set = Z_limit
    if Z_set < 0:
        Z_set = 0

    z_move = Z_set - Z_before
    if z_move > 0:               # jugg '+' or '-'
        MotorUP()
    else: 
        MotorDOWN()
        z_move = -z_move
    step_control(z_move)
    Z_before = Z_set

def step_move_fast():
    global Z_set
    global Z_before
    global Z_limit
    if Z_set > Z_limit:
        Z_set = Z_limit
    if Z_set < 0:
        Z_set = 0

    z_move = Z_set - Z_before
    if z_move > 0:               # jugg '+' or '-'
        MotorUP()
    else: 
        MotorDOWN()
        z_move = -z_move
    step_control_fast(z_move)
    Z_before = Z_set

def Gohome():
    global Z_before 
    global Z_set    
    #MotorUP()     #first, return to home, and set Z_set = 0
    #step_control(2.0) # go up 2mm incase hitting the board
    MotorDOWN()
    touch_value = GPIO.input(15)
    while(touch_value == 0):   #if touch == 1 stop , at home 11111111111
        GPIO.output(11 , GPIO.HIGH)
        time.sleep(0.000003)
        GPIO.output(11 , GPIO.LOW)
        time.sleep(0.000003)
        touch_value = GPIO.input(15)
    Z_before = 0
    Z_set    = 0
    Z_set = Z_set + 2.0
    step_move_fast()

    MotorDOWN()
    touch_value = GPIO.input(15)
    while(touch_value == 0):   #if touch == 1 stop , at home 22222222
        GPIO.output(11 , GPIO.HIGH)
        time.sleep(0.0001)
        GPIO.output(11 , GPIO.LOW)
        time.sleep(0.0001)
        touch_value = GPIO.input(15)
    Z_before = 0
    Z_set    = 0

def BigStep(direct):
    global Z_set
    if direct > 0:
        Z_set = Z_set + 5.0
        step_move()
    else:
        Z_set = Z_set - 5.0
        step_move()

def SmallStep(direct):
    global Z_set
    if direct > 0:
        Z_set = Z_set + 0.1
        step_move()
    else:
        Z_set = Z_set - 0.1
        step_move()


    
################ def USART ##############

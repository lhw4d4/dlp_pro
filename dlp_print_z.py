# import cv2
# import numpy as np
# import os,sys,stat
# import time
# import threading
# import RPi.GPIO as GPIO
#
#
# class Print(threading.Thread):
#     def __init__(self,dirname,exposure_time):
#         threading.Thread.__init__(self)
#         self.currentLayer = 0
#         self.totalLayer = 0
#         self.isfinishPrint = 0
#         self.dirname = dirname
#         self.stepper_init()
#         #for stepper
#         self.pitch = 2
#         self.stepper_pullback = 1
#         self.exposure_t = int(exposure_time*1000000)
#         self.stop=False
#
#     def run(self):
#         """ Print step1 : PNG and Stepper Init
#             Hail 409!
#         """
#
#         png_inputdir = self.dirname
#         name_filesvglog = self.dirname + '/print.log'
#         fn_svglog = open(name_filesvglog)
#         height = fn_svglog.readline()       #trans into float
#         height = height.strip('\n')
#         height_float = float(height)
#         fn_svglog.close()
#         stepper_pb = self.stepper_pullback  #
#         """ Print step2 : Show and Move
#             Hail 409!
#         """
#         self.isfinishPrint = 0
#         svg_num = 1
#         pic_x = 0
#         pic_y = 0
#         back_ground = cv2.imread("/home/pi/640-480.png")
#         blank_p = cv2.imread("/home/pi/640-480.png")
#         r_plus = 1.0  #multiple
#
#         self.MotorForward()     #first, move to the liquid
#         self.step_control(stepper_pb)
#         while 1:
#                 str1 = png_inputdir + "/"+ str(svg_num) + ".png"     #read png files in other
#                 img = cv2.imread(str1)
#                # if(img.shape >= back_ground.shape):
#                #     break
#                 img_r = cv2.resize(img,None,fx=r_plus,fy=r_plus,interpolation=cv2.INTER_CUBIC)#resize
#                 rows,cols,channels = img_r.shape
#                 back_ground[pic_x:rows, pic_y:cols] = img_r#copy
#                 cv2.namedWindow("image",cv2.WINDOW_NORMAL)
#                 cv2.setWindowProperty("image",0,1)
#                 cv2.imshow("image",back_ground)
#                 cv2.waitKey(self.exposure_t)   #
#                 #black  showoff
#                 #.......
#                 self.MotorReverse()
#                 self.step_control(stepper_pb + height_float)
#                 #.......
#                 cv2.imshow("image",blank_p)  #blank
#                 cv2.waitKey(1000)
#                 if self.stop:
#                     self.Gohome()
#                     break
#                 self.MotorForward()
#                 self.step_control(stepper_pb)
#                 return_key = cv2.waitKey(10)
#
#                 #print return_key
#                 if return_key == 27:            ##press 'ESC' to exit
#                     break
#                 if return_key == 113:           ##press 'q ' to pause
#                     return_key_continue = cv2.waitKey(0)
#                     #raw_input("Waiting for g to continue")
#                     return_key = 0
#                     pass
#                 svg_num += 1
#                 self.currentLayer = svg_num
#                 if svg_num == self.totalLayer:
#                     break
#         self.isfinishPrint = 1
#
#     def getcurrentLayer_print(self):
#         if (self.isfinishPrint == 1):
#             return -1
#         return self.currentLayer
#
#     def getTotalLayer(self):
#         png_inputdir = self.dirname
#         name_filesvglog = self.dirname + '/print.log'
#         fn_svglog = open(name_filesvglog)
#         height = fn_svglog.readline()       #trans into float
#         height = height.strip('\n')
#         height_float = float(height)
#         total = fn_svglog.readline()        #trans into int
#         total = total.strip('\n')
#         total_int = int(total)
#         self.totalLayer = total_int
#         fn_svglog.close()
#         return self.totalLayer
#
#     def stepper_init(self):
#         GPIO.setmode(GPIO.BOARD)
#         GPIO.setup(11,GPIO.OUT)     #pwm control
#         GPIO.setup(13,GPIO.OUT)     #direct control
#         GPIO.setup(15,GPIO.IN)      #home singal
#
#     def MotorForward(self):         #close to the liquid
#         GPIO.output(13 , GPIO.HIGH)
#
#     def MotorReverse(self):         #far from the liquid
#         GPIO.output(13 , GPIO.LOW)
#
#     def step_control(self,distance):
#         step_number = 6400 * distance / self.pitch
#         count = 0;
#         while (count < step_number):
#             GPIO.output(11 , GPIO.HIGH)
#             time.sleep(0.0001)
#             GPIO.output(11 , GPIO.LOW)
#             time.sleep(0.0001)
#             #print "outputing "
#             count = count + 1
#     def Gohome(self):
#         self.MotorReverse()
#         touch_value = GPIO.input(15)
#         while touch_value == 0:   #if touch == 1 stop , at home
#             GPIO.output(11 , GPIO.HIGH)
#             time.sleep(0.001)
#             GPIO.output(11 , GPIO.LOW)
#             time.sleep(0.001)
#             touch_value = GPIO.input(15)
#
#     def thread_stop(self):
#         self.stop = True

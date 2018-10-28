#!/usr/bin/env python
# coding=utf-8

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
#初始化gpio的电平，输入/输出模式
GPIO.setmode(GPIO.BOARD)
GPIO.setup(16,GPIO.OUT)     # for gpio  relay
GPIO.output(16,GPIO.LOW)    #relay

#初始化电机的pwm波口
GPIO.setup(12,GPIO.OUT)     # for pwm  steering
p_pwm = GPIO.PWM(12,50)
p_pwm.start(0)
p_pwm.ChangeDutyCycle(3.0)
time.sleep(2)
#GPIO.cleanup(12)

#初始化串口
ser = serial.Serial('/dev/ttyAMA0',9600,timeout=1)

print ser.isOpen()
#串口使能赋值
acerPowerOn  = "* 0 IR 001\r"
acerPowerOff = "* 0 IR 002\r"
#设置Z轴初始化参数
Z_before = 0
Z_set = 0
Z_layernow = 0

#设置Z轴长度，步进值，回退值（pull_back）,步进电机pwm参数
Z_limit = 250           #150
pitch = 4.0             #pitch   4.0, 8.0
pull_val = 2.0          #pull back   if you don want to pull back, set to 0.
stepper_open = 4.3      # stepoper_di:  45_degree : 4.3  / 90_degree : 6.8  / 135_degree : 9.3 


class Print(threading.Thread):
	#初始化曝光时间以及层高
    def __init__(self,dirname,exposure_time,height_in):
        threading.Thread.__init__(self)
        # 当前层数
        self.currentLayer = 0
        # 总共层数
        self.totalLayer = 0
        # 是否完成打印
        self.isfinishPrint = 0
        # 目录名
        self.dirname = dirname
        self.height = float(height_in)   #HEIGHT
        # 电机初始化
        stepper_init()
        # for stepper
        # 当前曝光时间
        self.exposure_trans = exposure_time
        self.stepper_pullback = pull_val   #2.0
        self.exposure_t = 0 #int(exposure_time*1000)
		#设置程序标志位
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
		#默认开始时关闭电机电源
        self.SteerPrintOff()              # do not let the light in!!
		#获取png文件路径以及层高
        png_inputdir = self.dirname       # a dir without '/' FROM user input!!
        height_float = self.height 
        #每次启动首先将电机拉回初始位置
        stepper_pb = self.stepper_pullback  #pull back each time
        """ Print step2 : Show and Move
            Hail 409!
        """
		#设置isfinish标志位为未完成
        self.isfinishPrint = 0    
        svg_num = 1
		#根据屏幕参数设置显示时的背景文件，以及用于切割的png文件的叠加文件
        back_ground = cv2.imread("/home/pi/1920-1080.png")
        blank_p = cv2.imread("/home/pi/1920-1080.png")
		#png文件缩放比例
        r_plus  = 1.0  
		#电机拉回初始位置
        Gohome()
		#设置Z轴相关参数
        Z_set = 0
        Z_before = 0
        Z_layernow = height_float * svg_num
        Z_set = Z_layernow
		#启动电机
        step_move()
		#获取png文件夹路径
        Png_files = os.listdir(self.dirname)
		#按照png文件的名称进行排序
        Png_files.sort()
      #  try:
           # os.system('rm ' + png_inputdir + '/Thumbs.db')
       #    print "haha"
       # except:
       #     pass
       # print self.exposure_trans
       #.......
        #设置屏幕显示程序句柄窗口，命名为image
        cv2.namedWindow("image",cv2.WINDOW_NORMAL)
		#设置image窗口为无菜单栏模式
        cv2.setWindowProperty("image",0,1)
		#显示背景图片（全黑）
        cv2.imshow("image",blank_p)
		#串口通讯开启
        ser.write(acerPowerOn)
        #cv2.waitKey(60000)
       #.......
		#电机开始运行
        self.SteerPrintOn()
		#循环显示相应的png文件
        for Png_name in Png_files:
				#如果png文件是前面3层，那么曝光时间是正常层曝光时间的三倍
                if svg_num <= 3:   #exposure time in first time is different
                    self.exposure_t = int(self.exposure_trans  *3)
                    #self.SteerPrintOn()
				#其他层按照正常曝光时间来计算
                else:
                    self.exposure_t = int(self.exposure_trans )    
				#获得png文件绝对路径
                str1 = png_inputdir + "/"+ Png_name
				#读取png文件到内存中
                img = cv2.imread(str1)                #
                # SHOW Image
				#重画png文件
                img_r = cv2.resize(img,None,fx=r_plus,fy=r_plus,interpolation=cv2.INTER_CUBIC)#resize
				#将重画的png文件显示在背景图片上
                cv2.imshow("image",img_r)
				#控制灯源开启
                self.RelayOn()
				#等待曝光
                cv2.waitKey(self.exposure_t)   # delay ms
#                self.RelayOff()        
				#如果是第一层，那么再多加一些曝光时间
                if svg_num == 1:
                    cv2.waitKey(200)
                    self.SteerPrintOn()
                    cv2.waitKey(self.exposure_t)
                # SHOW Black 
				#曝光结束，切换为全黑背景图
                cv2.imshow("image",blank_p)  #blank
				#灯源关闭
                self.RelayOff()
                cv2.waitKey(1)  #delay 1000  ,easy to change
                # Move UP
				#设置电机提升距离Z_set
                Z_set = Z_set + stepper_pb #+ height_float
				#电机拉起平台提升
                step_move()
                # Move DOWN
				#如果接收到了串口屏的暂停信号
                while self.suspend is True and self.stop is False:
                    time.sleep(0.5)
					#电机打印模式暂时关闭
                    self.SteerPrintOff()    #steering down 
				#如果接收到了串口屏的停止打印信号
                if self.stop:
                    self.currentLayer = -2
					#停止串口屏通讯
                    ser.write(acerPowerOff)
					#电机打印结束，拉高平台
                    self.MotorPrintOver()
					#电机打印模式关闭
                    self.SteerPrintOff()    #steering down 
                    break
				#设置当前层高
                Z_layernow = height_float * (svg_num + 1)
                Z_set = Z_layernow
				#电机正常移动
                step_move()
                #...
				#检查是否有键盘输入信号（调试时候使用）
                return_key = cv2.waitKey(1)
                
                #print return_key
				#如果按下‘ESC’那么退出程序，如果按下‘q’键那么暂停程序，如果按下空格键那么继续程序（调试程序时使用）
                if return_key == 27:            ##press 'ESC' to exit
                    break    
                if return_key == 113:           ##press 'q ' to pause
                    return_key_continue = cv2.waitKey(0)
                    #raw_input("Waiting for g to continue")
                    return_key = 0
                    pass
				#赋值当前层
                self.currentLayer = svg_num
                svg_num = svg_num + 1
				#如果打印完所有层
                if svg_num == self.totalLayer:
					#停止串口屏通讯
                    ser.write(acerPowerOff)
					#电机打印模式关闭
                    self.SteerPrintOff()      # control the steering
					#电机打印结束，拉高平台
                    self.MotorPrintOver()
					#初始化程序当前层为 -1 
                    self.currentLayer=-1
                    break
					
	#获取当前正在打印的层号
    def getcurrentLayer_print(self):
        return self.currentLayer
	#根据self.suspend参数确认是否暂停程序
    def thread_suspend(self):
        if self.suspend:
            self.suspend = False
        else:
            self.suspend = True
	#获取当前打印模型的总层数
    def getTotalLayer(self):
        #height
        dir_count = len( os.listdir(self.dirname) )
        self.totalLayer = dir_count
        return self.totalLayer
	
    #获取当前打印模型的总层数（通过log文件获取）
    def getTotalLayer2(self):
        png_inputdir = self.dirname       
		#设置log文件路径
        name_filesvglog = self.dirname + '/print.log'
		#打开log文件流
        fn_svglog = open(name_filesvglog)
		#按行读取log文件
        height = fn_svglog.readline()       #trans into float
		#以换行符确认是否一行
        height = height.strip('\n')
        height_float = float(height)
        total = fn_svglog.readline()        #trans into int
        total = total.strip('\n')
        total_int = int(total)
		#总层数
        self.totalLayer = total_int
		#关闭文件流
        fn_svglog.close()
		#返回总层数
        return self.totalLayer
    
	#根据参数self.stop，控制程序是否结束
    def thread_stop(self):
        self.stop=True
    
	#停止打印，将电机参数设置成初始值，并将打印平台快速拉高
    def MotorPrintOver(self):
        global Z_set
        global Z_limit
        global Z_before
        Z_set = Z_set + 50.0
        step_move_fast()

	#电机开始运行
    def SteerPrintOn(self):                
        GPIO.setmode(GPIO.BOARD)
        GPIO.setup(12,GPIO.OUT)
        p_pwm = GPIO.PWM(12,50)
        p_pwm.start(0)
        p_pwm.ChangeDutyCycle(stepper_open)             
        #GPIO.cleanup(12)
    
        #GPIO.output(16,GPIO.HIGH)
        time.sleep(2)
		
	#电机打印模式结束
    def SteerPrintOff(self):
        GPIO.setmode(GPIO.BOARD)
        GPIO.setup(12,GPIO.OUT)
        p_pwm = GPIO.PWM(12,50)
        p_pwm.start(0)
        p_pwm.ChangeDutyCycle(2.6)
        #GPIO.cleanup(12)
    
        #GPIO.output(16,GPIO.LOW)
        time.sleep(2)

	#灯源开启
    def RelayOn(self):             #light in  
        GPIO.output(16,GPIO.HIGH)
	
	#灯源关闭
    def RelayOff(self):
        GPIO.output(16,GPIO.LOW)

################ def Motor ###################


def stepper_init():
	#电机模式
    GPIO.setmode(GPIO.BOARD)
	#11口设置为pwm输出口
    GPIO.setup(11,GPIO.OUT)     #pwm control
	#13口设置为电机方向口
    GPIO.setup(13,GPIO.OUT)     #direct control 
	#电机标志口，读取
    GPIO.setup(15,GPIO.IN)      #home singal

#电机使能LOW，降
def MotorDOWN():         #close to the liquid
    GPIO.output(13 , GPIO.LOW)

#电机使能HIGH，升
def MotorUP():         #far from the liquid 
    GPIO.output(13 , GPIO.HIGH)

#根据移动的距离，操作电机移动
def step_control(distance):   #def for control step
    global pitch
	#计算需要步进电机转动的次数
    step_number = 6400 * distance / pitch
    count = 0
	#电机开始移动
    while count < step_number:
        GPIO.output(11 , GPIO.HIGH)
        time.sleep(0.00005)
        GPIO.output(11 , GPIO.LOW)
        time.sleep(0.00005)
        #print "outputing "
        count = count + 1    

#根据移动的距离，操作电机快速移动（time.sleep数值减小）
def step_control_fast(distance):   #def for control step
    global pitch
    step_number = 6400 * distance / pitch
    count = 0
    while count < step_number:
        GPIO.output(11 , GPIO.HIGH)
        time.sleep(0.00001)
        GPIO.output(11 , GPIO.LOW)
        time.sleep(0.00001)
        #print "outputing "
        count = count + 1    

#根据全局变量Z_set,移动电机位置到指定的Z_set值（相对位置）
def step_move():
    global Z_set
    global Z_before
    global Z_limit
	#如果Z_set数值超过限制区间值，那么设置为边缘值
    if Z_set > Z_limit:
        Z_set = Z_limit
    if Z_set < 0:
        Z_set = 0
	#计算电机方向
    z_move = Z_set - Z_before
	#移动数据大于0上升
    if z_move > 0:               # jugg '+' or '-'
        MotorUP()
	#移动数据小于0下降
    else: 
        MotorDOWN()
        z_move = -z_move
	#电机移动
    step_control(z_move)
	#将之前的Z轴坐标设置为当前坐标
    Z_before = Z_set

#电机快速运动
def step_move_fast():
    global Z_set
    global Z_before
    global Z_limit
	#如果Z_set数值超过限制区间值，那么设置为边缘值
    if Z_set > Z_limit:
        Z_set = Z_limit
    if Z_set < 0:
        Z_set = 0
	#计算电机方向
    z_move = Z_set - Z_before
	#移动数据大于0上升
    if z_move > 0:               # jugg '+' or '-'
        MotorUP()
	#移动数据小于0下降
    else: 
        MotorDOWN()
        z_move = -z_move
	#电机快速移动
    step_control_fast(z_move)
	#将之前的Z轴坐标设置为当前坐标
    Z_before = Z_set


def Gohome():
    global Z_before 
    global Z_set    
    #MotorUP()     #first, return to home, and set Z_set = 0
    #step_control(2.0) # go up 2mm incase hitting the board
	#使能方向向下
    MotorDOWN()
	#平台是否触碰到限位开关，读取限位开关的数值
    touch_value = GPIO.input(15)
    while True:   #if touch == 1 stop , at home 11111111111
        GPIO.output(11 , GPIO.HIGH)
        time.sleep(0.000003)
        GPIO.output(11 , GPIO.LOW)
        time.sleep(0.000003)
        touch_value = GPIO.input(15)
		#如果平台触碰到了限位开关，那些稍等一会，以防止电流紊乱导致的限位开关误触
        if touch_value == 1:
            time.sleep(0.05)
			#限位开关不是误触，确认平台到达指定位置，退出循环
            if touch_value == 1:
                break
    Z_before = 0
    Z_set = 0
    Z_set = Z_set + 5.0
	#平台在Z轴快速移动
    step_move_fast()

    MotorDOWN()
	#平台是否触碰到限位开关，读取限位开关的数值
    touch_value = GPIO.input(15)
	#微调平台
    while True:   #if touch == 1 stop , at home 22222222
        GPIO.output(11 , GPIO.HIGH)
        time.sleep(0.0001)
        GPIO.output(11 , GPIO.LOW)
        time.sleep(0.0001)
        touch_value = GPIO.input(15)
        if touch_value == 1:
            time.sleep(0.05)
            if touch_value == 1:
                break;
    Z_before = 0
    Z_set = 0

#快速的步进电机速度
def BigStep(direct):
    global Z_set
	#确认电机的转动方向
    if direct > 0:
        Z_set = Z_set + 5.0
        step_move()
    else:
        Z_set = Z_set - 5.0
        step_move()

#慢速的步进电机速度
def SmallStep(direct):
    global Z_set
    if direct > 0:
        Z_set = Z_set + 0.1
        step_move()
    else:
        Z_set = Z_set - 0.1
        step_move()




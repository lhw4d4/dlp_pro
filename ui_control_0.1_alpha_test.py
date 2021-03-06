#!/usr/bin/env python
# coding=utf-8
import datetime
import serial
import os
import time
import threading
import Queue
from dlp_slice import Slice
from dlp_print import *

def device_write(device,strl):
    try:
        device.write(strl)
    except SerialException,e:
        print e
        device.close()
        return -1
    else:
        return 0 

class Consumer(threading.Thread):
    def __init__(self,thread1,device):
        threading.Thread.__init__(self)
        self.device=device
        self.suspend=False
	self.thread1=thread1
        self.stop=False
        
    def run(self):
        timespent=0
	totallayer=self.thread1.getTotalLayer()
	print "totallayer: ",totallayer
	self.device.write("""n0.val=%d\xff\xff\xff"""%totallayer) 
        while True:
            if self.stop:
                break
            result=self.thread1.getcurrentLayer_print()
            if result==0:
                self.device.write("""t4.txt="%d"\xff\xff\xff"""%timespent)
	    else:
		if result==-2:
	            break
		if result==-1:
	            self.device.write("""page 7\xff\xff\xff""")
		    break
                self.device.write("""n1.val=%d\xff\xff\xff"""%result)
                self.device.write("""j0.val=%d\xff\xff\xff"""%(result*100/totallayer))
                self.device.write("""t4.txt="%d"\xff\xff\xff"""%timespent)
	    time.sleep(1)
	    timespent=timespent+1
    
    def thread_suspend(self):
        self.suspend=True

    def thread_restart(self):
        self.suspend=False

    def thread_stop(self):
        self.stop=True


#16进制转换函数
def hex(argv):
    result=[]
    hlen=len(argv)
    for i in xrange(hlen):
        hvol=ord(argv[i])
        hhex='%02x' % hvol
        result.append(hhex)
    return result

def getfile_stl(filepath):
    current_files=os.listdir(filepath)
    all_file=[]
    for filename in current_files:
        full_file_name=os.path.join(filepath,filename)
        if os.path.isdir(full_file_name):
            all_file.append(filename)
        if filename.endswith(".stl"):
            all_file.append(filename)
   # all_file.append(".")
    all_file.append("<<===||")
    return all_file

def getfile_svg(filepath):
    current_files=os.listdir(filepath)
    all_file=[]
    for filename in current_files:
        full_file_name=os.path.join(filepath,filename)
	if os.path.isdir(full_file_name):
	    all_file.append(filename)
   # all_file.append(".")
    all_file.append("<<===||")
    return all_file


#串口初始化程序
def ui_control(port,boud):
	#打印用参数初始化
    speed=0
    upheight=0
    slice_path=""
    print_path=""
    sliceorprint=0
    height=0
    timeinterval=0
    scale=1
    totalfile=""
    slicefile=''
    slice_file=""
    print_file=""
    totallayer=0
	#初始化电机
    stepper_init()
    try:		
	#尝试进行串口连接
        device=serial.Serial(port,boud)
    except serial.serialutil.SerialException,e:
        print e
        return
    device.flushInput()
    device.flushOutput()
	#向串口写入数据
    device.write("""page 1\xff\xff\xff""")
    while True:
	try:
		#串口读取数据
        str=device.read(6)
	except serial.portNotOpenError:
		#如果串口被以外关闭，丢弃连接
	    print "error happen"
	    device.close()
   	    break
	else:
		#以16进制转换数据
            result=hex(str)
            print result
            var=result[1]
            if result[0]=='00':
                if var=='00':
		    if sliceorprint==1:
			slice_path='/media'
                        slice_file=getfile_stl(slice_path)
		 	print slice_file
                        num=len(slice_file)
                        i=0
                        flag=1
                        number=int(result[2],16)
                        while i<5:
                            if(number<num):
                                print "t%d.txt=\"%s\"\xff\xff\xff" %(i,slice_file[number])
                                device.write("""t%d.txt="%s"\xff\xff\xff""" %(i,slice_file[number]))
                            else:
                                if(flag):
                                    device.write("""t%d.txt="__over__"\xff\xff\xff""" % i)
                                    flag=0
                                else:
                                    device.write("""t%d.txt=" "\xff\xff\xff""" % i) 
                            number=number+1
                            i=i+1
		    if sliceorprint==2:
			print_path='/media'
                        print_file=getfile_svg(print_path)
                        num=len(print_file)
                        i=0
                        flag=1
                        number=int(result[2],16)
                        while i<5:
                            if(number<num):
                                print "t%d.txt=\"%s\"\xff\xff\xff" %(i,print_file[number])
                                device.write("t%d.txt=\"%s\"\xff\xff\xff" %(i,print_file[number]))
                    	    else:
                                if(flag):
                                    device.write("t%d.txt=\"over\"\xff\xff\xff" % i)
                                    flag=0
                                else:
                                    device.write("t%d.txt=\" \"\xff\xff\xff" % i)
                            number=number+1
                            i=i+1
		elif var=="11":
		    sliceorprint=int(result[2],16)
		elif var=='10':
		    flag=1
		    if sliceorprint==1:
  		        num=len(slice_file)
		        print slice_file
		        number=int(result[2],16)
		        for i in range(5):
			    if number<num:
			        device.write("""t%d.txt="%s"\xff\xff\xff""" %(i,slice_file[number]))
			    else:                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                 
  			        if flag:
				    device.write("""t%d.txt="__over__"\xff\xff\xff"""%i)
				    flag=0
			        else:
				    device.write("""t%d.txt=""\xff\xff\xff"""%i)
                            number=number+1
		    if sliceorprint==2:
  		        num=len(print_file)
		        number=int(result[2],16)
		        for i in range(5):
			    if number<num:
			        device.write("""t%d.txt="%s"\xff\xff\xff""" %(i,print_file[number]))
			    else:                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                 
  			        if flag:
				    device.write("""t%d.txt="__over__"\xff\xff\xff"""%i)
				    flag=0
			        else:
				    device.write("""t%d.txt=""\xff\xff\xff"""%i)
			    number=number+1
                elif var=='01':
		    if sliceorprint==1:
                        flag=1
                        postfile=slice_file[int(result[2],16)]
                        keepfile=postfile
                        if postfile=="<<===||":
			    totalfile=os.path.split(slice_path)[0]
                        elif postfile==".":
                            pass
                        else:
                            totalfile=os.path.join(slice_path,postfile)
                        if os.path.isdir(totalfile):
                            if totalfile!="/":
                                slice_path=totalfile+'/'
                            else:
                                slice_path=totalfile
			    slice_file=getfile_stl(slice_path)
                            for i in range(5):
                                if i<len(slice_file):
                                    device.write("""t%d.txt=\"%s\"\xff\xff\xff"""%(i,slice_file[i]))
                                elif flag:
                                    print """t%d.txt=\"__over__\"\xff\xff\xff"""%i
                                    device.write("""t%d.txt=\"__over__\"\xff\xff\xff"""%i)
                                    flag=0
                                else:
                                    device.write("""t%d.txt=\" \"\xff\xff\xff"""%i)
		    if sliceorprint==2:
                        flag=1
                        postfile=print_file[int(result[2],16)]
                        keepfile=postfile
                        if postfile=="<<===||":
			    totalfile=os.path.split(print_path)[0]
                        elif postfile==".":
                            pass
                        else:
                            totalfile=os.path.join(print_path,postfile)
                        print print_path
                        print totalfile
                        if os.path.isdir(totalfile):
                            if totalfile!="/":
                                print_path=totalfile
                            else:
                                print_path=totalfile
                            # print "mm",print_path
			    print_file=getfile_stl(print_path)
			    print print_file
                            for i in range(5):
                                if i<len(print_file):
                                    device.write("""t%d.txt=\"%s\"\xff\xff\xff"""%(i,print_file[i]))
                                elif flag:
                                    print """t%d.txt=\"over\"\xff\xff\xff"""%i
                                    device.write("""t%d.txt=\"__over__\"\xff\xff\xff"""%i)
                                    flag=0
                                else:
                                    device.write("""t%d.txt=\" \"\xff\xff\xff"""%i)
                            
                elif var=="15":
                    if sliceorprint == 1:
                        postfile = slice_file[int(result[2],16)]
                        totalfile=os.path.join(slice_path,postfile)
                        slicefile=totalfile
                        device.write("""page 8\xff\xff\xff""")
                        device.write("""t1.txt="%s"\xff\xff\xff"""% postfile)
                    if sliceorprint == 2:
                        postfile=print_file[int(result[2],16)]
                        totalfile=os.path.join(print_path,postfile)
                        printfile=totalfile
                        device.write("""page 11\xff\xff\xff""")
                        device.write("""t1.txt="%s"\xff\xff\xff"""%postfile)
                elif var=='02':
                    if sliceorprint==1:
                        device.write("t1.txt=\"%s\"\xff\xff\xff" % os.path.split(slicefile)[1])
                    else:
                        device.write("t1.txt=\"%s\"\xff\xff\xff" % os.path.split(printfile)[1])
                elif var=='03':
                    print "suspend"
                    t0.thread_suspend()
                elif var=='04':
                    print "start"
                    t0.thread_suspend()
                elif var=='05':
                    print "stop"
                    t0.thread_stop()
                    t1.thread_stop()
                elif var=='06':
                    print "restart"
                elif var=='07':
                    device.write("""page 4\xff\xff\xff""")
                elif var=='0e':    
                    t0=Print(printfile,timeinterval,layerheight)
                    t1=Consumer(t0,device)
                    device.write("j0.val=0\xff\xff\xff")
                    device.write("n1.val=0\xff\xff\xff")
                    t0.start()
                    t1.start()
                elif var=='08':
                    print "slice start"
	            height=float(height)*0.001
	            print slicefile,height
	            sli=Slice(slicefile,height)
	            sli.start()
                    while True:
                        time.sleep(0.5)
                        currentlayer=sli.getcurrentLayer()
		        totallayer=sli.getTotalLayer()
		        if currentlayer>0:
		  	    tmp=(currentlayer*100)/totallayer
			    device.write("""j0.val=%d\xff\xff\xff"""%tmp)
                	    device.write("""t1.txt=\"%s/%s\"\xff\xff\xff"""%(currentlayer,totallayer))
		        if currentlayer==-1:
			    device.write("""j0.val=100\xff\xff\xff""")
			    device.write("""t1.txt="%d/%d"\xff\xff\xff"""%(totallayer,totallayer))
			    device.write("""vis b0,1\xff\xff\xff""")
			    break

                elif var=="09":
                    device.write("""t0.txt="h:%d"\xff\xff\xff"""%height)
                    device.write("""t1.txt="t:%d"\xff\xff\xff"""%speed)
                    device.write("""t2.txt="s:%.02f"\xff\xff\xff"""%upheight)
                elif var=="0a":
                    height=int(result[3],16)*256+int(result[2],16)
                    print "height:",height
                elif var=="0b":
		    speed=int(result[3],16)*256+int(result[2],16)
		    print "speed:",speed
                elif var=="0c":
                    upheight=int(result[3],16)*256+int(result[2],16)
                    print "upheight:",upheight
		elif var=="0d":
		    timeinterval=int(result[3],16)*256+int(result[2],16)
                    timeinterval=float(timeinterval)
                    print "timeinterval:",timeinterval
	        elif var=="0f":
	            slice_file=[]
		    print_file=[]
                elif var=="12":
                    
                    device.write("""vis b0,0\xff\xff\xff""")
                    device.write("""vis b3,0\xff\xff\xff""")
                    Gohome()
                    
                    device.write("""vis b0,1\xff\xff\xff""")
                    device.write("""vis b3,1\xff\xff\xff""")
                elif var=="13":
                    if int(result[2],16)==1:
                        BigStep(1)
                    elif int(result[2],16)==0:
                        BigStep(0)
                elif var=="14":
                    if int(result[2],16)==1:
                        SmallStep(1)
                    elif int(result[2],16)==0:
                        SmallStep(0)
                elif var=="16":
                    layerheight = int(result[3],16)*256+int(result[2],16)
                    layerheight = float(layerheight)/1000
                    print "layerheight:",layerheight
                elif var=="17":
                    device.write("""t0.txt="%f"\xff\xff\xff"""%layerheight)
                    device.write("""t1.txt="%f"\xff\xff\xff"""%timeinterval)
                else:
                    print str
                    device.close()
                    break
	    else:
	        print "recv error!"
	        device.close()


    

if __name__=='__main__':
	#循环
    while True:
	device_name = None
	#在树莓派的USB设备中寻找U盘设备
        for uartfile in os.listdir("/dev"):
		#如果设备名字是ttyusb，那么确认找到
            if uartfile.startswith("ttyUSB"):
            	device_name="/dev/"+uartfile
	if device_name != None:
	    print device_name
		#如果找到了U盘设备，那么初始化电机串口
        ui_control(device_name,9600)
	    print "run error"
            
	else:
        print "over"
		#2秒轮询
  	    time.sleep(2)
            





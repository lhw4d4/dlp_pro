#!/usr/bin/env python
# coding=utf-8

import cairosvg
import os,sys,stat
import threading


class Slice(threading.Thread):
	#初始化切割的文件名，层高等参数
    def __init__(self,filename,height):
        threading.Thread.__init__(self)
        self.filename=filename
        self.height=height
        self.currentLayer=0
        self.isfinishslic=0
        self.totalLayer = 0

	#切割主函数
    def run(self):
        """ Slice step1 : STL -> SVG ;  
            From /U/xxx.stl -> /home/pi/DLP_svg/xxx.svg

            Hail 409!
        """
        chosen_path = self.filename   #load and store the filename
        self.isfinishslic = 0       #a finish flag    
		#将.stl文件利用slic3r命令行切割成.svg文件
        os.system('/home/pi/Slic3r/slic3r.pl '+ self.filename + ' --layer-height ' + str(self.height) +' --export-svg --output /home/pi/DLP_svg/')        

        """ Slice step2 : SVG -> PNG ;  
            From  /home/pi/DLP_svg/xxx.svg -> /home/pi/DLP_png/xxx/1,2,3
            Hail 409!
        """
        chosen_namestl = chosen_path.split('/')[-1]             #xxx.stl
        chosen_name    = chosen_namestl.split('.')[0]           #xxx
        chosen_namesvg = chosen_name + '.svg'                   #xxx.svg
        #设置切割好的.svg文件         
        svg_inputdir = os.path.join("/home/pi/DLP_svg/",chosen_namesvg)             #get the svg_outputdir above  /home/pi/DLP_svg/xxx.svg
		#创建.png文件输出路径（文件夹）
        png_outputdir = "/home/pi/DLP_png/" + chosen_name + '/'                    #create a png_outputdir   /home/pi/DLP_png/xxx/
        try:
			#如果之前已经创建了文件夹，那么清空
            os.system('rm -rf ' + png_outputdir)
        except:
            pass
        os.mkdir(png_outputdir)
		#加载.SVG文件
        fn_svg = open(svg_inputdir)             #open the svg_inputdir
        num = 1                                 #count for the png
        whole = fn_svg.read()
		#计算.SVG文件所带层数
        split_list = whole.split('<g ')         #before trans for the pngs
        split_len  = len(split_list) 
		#设置第一个svg层块
        head = split_list[0]
        mid = "<g "
        tail = "</svg>"
        #解析svg层块，并将之输出为png文件
        while 1:
                print "This is ",  num, " :" 
                try:
						#如果是最后一个svg块，那么不加文件尾巴
                        if num == ( split_len - 1 ):
                                file_x = head + mid + split_list[num]
						#非最后一个svg文件块
                        else:
                                file_x = head + mid + split_list[num] + tail
						#png文件输出路径
                        exportPath = os.path.join( png_outputdir, str(num) + ".png")
						#svg文件块转换成png文件
                        cairosvg.svg2png(bytestring=file_x, write_to=exportPath)
                except Exception as e: 
                        print e                                                            
                        pass
				#记录当前层数
                self.currentLayer = num
                self.totalLayer = split_len
                num += 1
				#如果层数到达最大，退出当前循环
                if num == split_len:
                        break
        #create a log file to store <height> <total>     /home/pi/DLP_png/xxx/print.log
		#初始化已经被切割好的文件的层高和层数
        trans_height = str(self.height) + '\n'
        trans_total  = str(split_len) + '\n'
        newlogname = png_outputdir + 'print.log'
        #newlogname = os.path.join( png_outputdir, 'print.log')   ## maybe use os.path.join
		#创建log文件来记录层高和总层数
        fn_pnglog = open(newlogname, 'w')
        fn_pnglog.write(trans_height)       #first  line : height
        fn_pnglog.write(trans_total)        #second line : total

		#完成切割，关闭svg文件流
        print "Finish!!!!"
        fn_svg.close()
		#完成标志位
        self.isfinishslic = 1
        
	#获取当前层数
    def getcurrentLayer(self):
        if (self.isfinishslic == 1):
            return -1
        return self.currentLayer
    
	#获取总层数
    def getTotalLayer(self):
        return self.totalLayer


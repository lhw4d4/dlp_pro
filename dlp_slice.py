#!/usr/bin/env python
# coding=utf-8

import cairosvg
import os,sys,stat
import threading


class Slice(threading.Thread):
    def __init__(self,filename,height):
        threading.Thread.__init__(self)
        self.filename=filename
        self.height=height
        self.currentLayer=0
        self.isfinishslic=0
        self.totalLayer = 0

    def run(self):
        """ Slice step1 : STL -> SVG ;  
            From /U/xxx.stl -> /home/pi/DLP_svg/xxx.svg

            Hail 409!
        """
        chosen_path = self.filename   #load and store the filename
        self.isfinishslic = 0       #a finish flag    
        os.system('/home/pi/Slic3r/slic3r.pl '+ self.filename + ' --layer-height ' + str(self.height) +' --export-svg --output /home/pi/DLP_svg/')        

        """ Slice step2 : SVG -> PNG ;  
            From  /home/pi/DLP_svg/xxx.svg -> /home/pi/DLP_png/xxx/1,2,3
            Hail 409!
        """
        chosen_namestl = chosen_path.split('/')[-1]             #xxx.stl
        chosen_name    = chosen_namestl.split('.')[0]           #xxx
        chosen_namesvg = chosen_name + '.svg'                   #xxx.svg
                 
        svg_inputdir = os.path.join("/home/pi/DLP_svg/",chosen_namesvg)             #get the svg_outputdir above  /home/pi/DLP_svg/xxx.svg

        png_outputdir = "/home/pi/DLP_png/" + chosen_name + '/'                    #create a png_outputdir   /home/pi/DLP_png/xxx/
        try:
            os.system('rm -rf ' + png_outputdir)
        except:
            pass
        os.mkdir(png_outputdir)

        fn_svg = open(svg_inputdir)             #open the svg_inputdir
        num = 1                                 #count for the png
        whole = fn_svg.read()
        split_list = whole.split('<g ')         #before trans for the pngs
        split_len  = len(split_list) 
        head = split_list[0]
        mid = "<g "
        tail = "</svg>"
        
        while 1:
                print "This is ",  num, " :" 
                try:
                        if num == ( split_len - 1 ):
                                file_x = head + mid + split_list[num]
                        else:
                                file_x = head + mid + split_list[num] + tail

                        exportPath = os.path.join( png_outputdir, str(num) + ".png")
                        cairosvg.svg2png(bytestring=file_x, write_to=exportPath)
                except Exception as e: 
                        print e                                                            
                        pass
                self.currentLayer = num
                self.totalLayer = split_len
                num += 1
                if num == split_len:
                        break
        #create a log file to store <height> <total>     /home/pi/DLP_png/xxx/print.log
        trans_height = str(self.height) + '\n'
        trans_total  = str(split_len) + '\n'
        newlogname = png_outputdir + 'print.log'
        #newlogname = os.path.join( png_outputdir, 'print.log')   ## maybe use os.path.join
        fn_pnglog = open(newlogname, 'w')
        fn_pnglog.write(trans_height)       #first  line : height
        fn_pnglog.write(trans_total)        #second line : total

        print "Finish!!!!"
        fn_svg.close()
        self.isfinishslic = 1
        
    def getcurrentLayer(self):
        if (self.isfinishslic == 1):
            return -1
        return self.currentLayer
    
    def getTotalLayer(self):
        return self.totalLayer


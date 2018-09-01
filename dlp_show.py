import cv2
import numpy as np



svg_num = 1

pic_x=10
pic_y=10#place
back_ground = cv2.imread("/home/pi/1280-1024.png")
cv2.waitKey(500)
svg_num = 1
r_plus = 5.0

while 1:
        str1 = outputdir + "/"+ str(svg_num) + ".png"
        img = cv2.imread(str1)
	if(img.shape >= back_ground.shape):
		break
        img_r = cv2.resize(img,None,fx=r_plus,fy=r_plus,interpolation=cv2.INTER_CUBIC)#resize
        rows,cols,channels = img_r.shape
        back_ground[pic_x:rows+pic_x, pic_y:cols+pic_y] = img_r#copy
        cv2.namedWindow("image",cv2.WINDOW_NORMAL)
        cv2.setWindowProperty("image",0,1)
        cv2.imshow("image",back_ground)
        return_key = cv2.waitKey(10)
     
        #print return_key
        if return_key == 27:            ##press 'ESC' to exit
            break    
        if return_key == 113:           ##press 'q ' to pause
            return_key_continue = cv2.waitKey(0)
            #raw_input("Waiting for g to continue")
            return_key = 0
            pass

        svg_num += 1
        if svg_num == split_len:
            break

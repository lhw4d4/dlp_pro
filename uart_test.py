#串口测试代码
import serial
import time

ser = serial.Serial('/dev/ttyAMA0',9600,timeout=1)

print ser.isOpen()
words_on = [0xBE,0xEF,0x03,0x19,0x00,0x83,0xA9,0x01,0x23,0x03,0xcc,0xcc,0xff,0xff,0xff,0xff,
    0x01,0x00,0x00,0x00,0xcc,0xcc,0xcc,0xcc,0xcc,0xcc,0xcc,0xcc,0xcc,0xcc,0xcc,0xcc]

words_off = [0xBE,0xEF,0x03,0x19,0x00,0x13,0x68,0x01,0x23,0x03,0xcc,0xcc,0xff,0xff,0xff,0xff,
    0x01,0x00,0x00,0x00,0xcc,0xcc,0xcc,0xcc,0xcc,0xcc,0xcc,0xcc,0xcc,0xcc,0xcc,0xcc]

acerPowerOn = "* 0 IR 001\r"
acerPowerOff = "* 0 IR 002\r"


ser.write(acerPowerOn)
time.sleep(2)
print "send over"

while 1:
    getchr = ser.read()
    print getchr

ser.close()

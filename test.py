import serial
<<<<<<< HEAD
s = serial.Serial("/dev/tty.wchusbserial1420", baudrate=38400, timeout=3.0)
print s.write("\x56\x00\x11\x00")
d = s.read(size=16)
res = []
for ch in d[:5]:
    res.append(ord(ch))
res.append(d[5:])
print res
=======
from camera_ttl import reply2hex

s = serial.Serial("/dev/ttyAMA0", baudrate=115200, timeout=1.5)
s.write([0x7E, 0x00, 0x08, 0x00, 0x01, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x09, 0xE7])
# s.write([0x7E, 0x00, 0x08, 0x00, 0x03, 0x05, 0x00, 0x01, 0x00, 0x00, 0x00, 0x11, 0xE7])
r = s.readline()
print len(r)
print reply2hex(r)
s.close()
>>>>>>> 70d19a34c697259bdfebcef43411d67a97039363

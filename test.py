import serial
from camera_ttl import reply2hex

s = serial.Serial("/dev/ttyAMA0", baudrate=57600, timeout=1.0)
s.write([0x7E, 0x00, 0x08, 0x00, 0x01, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x09, 0xE7])
# s.write([0x7E, 0x00, 0x08, 0x00, 0x03, 0x04, 0x00, 0x01, 0x00, 0x00, 0x00, 0x10, 0xE7])
r = s.read(size=20)
print len(r)
print reply2hex(r)
s.close()

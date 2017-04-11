import serial
s = serial.Serial("/dev/tty.wchusbserial1420", baudrate=38400, timeout=3.0)
print s.write("\x56\x00\x11\x00")
d = s.read(size=16)
res = []
for ch in d[:5]:
    res.append(ord(ch))
res.append(d[5:])
print res

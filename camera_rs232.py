import binascii
import serial
import time


BAUD = 38400
PORT = "/dev/tty.wchusbserial1410"
TIMEOUT = 5.0


class CameraSerial232(serial.Serial):

    def GET_VERSION(self):
        """
        Get the firmware version of the camera, the last item of the return list is the version string
        :return:
        """
        self.write("\x56\x00\x11\x00")
        d = self.read(size=16)
        res = []
        for ch in d[:5]:
            res.append(ord(ch))
        res.append(d[5:])
        return res

    def _FBUF_CTRL(self, reset=False):
        if reset:
            cmd = "\x56\x00\x36\x01\x02"
        else:
            cmd = "\x56\x00\x36\x01\x00"

        self.write(cmd)
        d = self.read(size=5)
        if ord(d[3]) == 3:
            return False
        else:
            return True

    def _GET_FBUF_LEN(self):
        cmd = "\x56\x00\x34\x01\x00"
        self.write(cmd)
        d = self.read(size=9)
        if ord(d[3]) == 3:
            return False
        else:
            int_fbuf_len = int(''.join(binascii.hexlify(ch) for ch in d[5:]), 16)
            print "Total length of the buffer:", int_fbuf_len
            self._hex_fbuf_len = d[5:]
            self._int_fbuf_len = int_fbuf_len
            return True

    def _hexlify(self, unicode):
        return ' '.join(binascii.hexlify(ch) for ch in unicode)


    def _READ_FBUF(self):
        '''
        frametype: 0x00
        action: 0x0F
        start_address: 0x00
        length: GET_FBUF_LEN
        delaytime: default=3000
        :return:
        '''
        cmd = ("\x56\x00\x32\x0c\x00\x0a\x00\x00\x00\x00" +
               self._hex_fbuf_len + "\x00\x00")
        self.write(cmd)
        d = self.read(size=5)
        print "READ_FBUF returns:", ' '.join(binascii.hexlify(ch) for ch in d)
        if ord(d[3]) != 0:
            return False
        else:
            time.sleep(0.03)
            img_d = self.read(size=self._int_fbuf_len)
            print "Length of bytes returned:", len(img_d)
            print "Info returned:", ' '.join(binascii.hexlify(ch) for ch in img_d)
            time.sleep(0.03)
            d = self.read(size=5)
            print self._hexlify(d)
            # if ord(d[3]) != 0:
            #     return False

            self._img_d = img_d
            print "Reset webcam"
            self._FBUF_CTRL(reset=True)
            return True

    def take_picture(self, fn):
        if self._FBUF_CTRL():
            self._hex_fbuf_len = ""
            self._int_fbuf_len = 0
            if self._GET_FBUF_LEN():
                self._img_d = ""
                if self._READ_FBUF():
                    self._save_img(fn)
                    return True
                else:
                    print "READ_FBUF error!"
            else:
                print "GET_FBUF_LEN error!"
        else:
            print "FBUF_CTRL error!"
        return False

    def _save_img(self, fn):
        """
        Save the image
        :param photo:
        :param fn:
        :return:
        """
        try:
            f = open(fn, 'w')
            f.write(self._img_d)
            f.close()
            self._img_d = ""
        except:
            pass

    def resize(self, large=False):
        """
        Change resolution of picture
        :param large: boolean, True is 640x480, False is 320x240
        :return:
        """
        if large:
            cmd = "\x56\x00\x31\x05\x04\x01\x00\x19\x00"
        else:
            cmd = "\x56\x00\x31\x05\x04\x01\x00\x19\x11"

        self.write(cmd)
        d = self.read(size=5)
        if d != "\x76\x00\x31\x00\x00":
            print "Resize image failed!"
            return False
        else:
            print "Resize image succeeded!"
            return True

    def set_baudrate(self, baudrate):
        baudrate_dict = {9600: "\xAE\xC8",
                         19200: "\x56\xE4",
                         38400: "\x2A\xF2",
                         57600: "\x1c\x4c",
                         115200:"\x0d\xa6"}
        cmd = "\x56\x00\x24\x03\x01" + baudrate_dict[baudrate]
        self.write(cmd)
        d = self.read(size=5)
        if d != "\x76\x00\x24\x00\x00":
            print "Set baudrate failed!"
            return False
        else:
            print "Set baudrate succeeded!"
            self.baudrate = baudrate
            return True


def main():
    camSerial = CameraSerial232(PORT, baudrate=BAUD, timeout=TIMEOUT)
    try:
        print camSerial.GET_VERSION()
        camSerial.resize()
        camSerial.take_picture("photo_rs232.jpg")
        camSerial.close()
    except:
        camSerial.close()

if __name__ == "__main__":
    main()
import binascii
import serial

# Default settings, these could be changed
BAUD = 115200
PORT = "/dev/tty.wchusbserial1410"
TIMEOUT = 1.2


# Default command code, global variables
# Get configuration info
CMD_GETVERSION = 0x01

# Configure camera settings
CMD_CONFIG = 0x03

# Adjust camera focus
CMD_FOCUS = 0x09

# Take one single picture
CMD_TAKEPIC = 0x05

# Upload picture to host
CMD_UPLOAD = 0x07


# Default parameter code
# NaN parameters
PARAM_EMPTY = 0x00

# Baudrate configuration dictionary
baudrate_dict = {9600: 0x01, 19200: 0x02,
                 38400: 0x03, 57600: 0x04,
                 115200: 0x05, 230400: 0x06,
                 460800: 0x07, 921600: 0x08}

# Packet size configuration dictionary
packet_dict = {256: 0x01, 512: 0x02,
               1024: 0x03, 2048: 0x04}


def int2hexList(val):
    """
    Convert a integer to a 2 bytes hex values list
    :param val: integer
    :return: a list of integers convert from hex
    """
    hex_str = "{0:#0{1}x}".format(val, 6)[2:]
    return [int(hex_str[:2], 16), int(hex_str[2:], 16)]


def format_cmd_hex(cmd, params):
    """
    Deprecated, this won't work in Python
    :param cmd: a hex for command
    :param params: 6 hexes for command parameters
    :return: return a send command string
    """

    send_command = "\x7E\x00\x08\x00" + chr(cmd) + ''.join(chr(param) for param in params)
    checksum = sum(bytearray(send_command[1:])) % 256
    send_command += chr(checksum) + chr(0xE7)
    send_command_hex = ' '.join(binascii.hexlify(ch) for ch in send_command)
    return send_command_hex


def format_cmd(cmd, params):
    """
    Format the commands into a list of integers
    \x7E\x00\x08\x00 is the header for the camera
    \xE7 is the tail for the camera
    checksum is defined as the sum of the 2nd byte to the 11th byte mod 256
    The command
    :param cmd:
    :param params:
    :return: return a list of commands
    """

    # Header are always \x7E\x00\x08\x00
    # Tail is checksum + \xE7
    send_command = "\x7E\x00\x08\x00" + chr(cmd) + ''.join(chr(param) for param in params)

    # Compute checksum
    checksum = sum(bytearray(send_command[1:])) % 256

    # Format the list of hex bytes
    send_command_list = []
    for c in send_command:
        send_command_list.append(ord(c))
    send_command_list += [checksum, int('E7', 16)]
    return send_command_list


def reply2hex(reply):
    """
    Parse the replied unicode to a string with hex bytes separated by space
    :param reply: unicode
    :return: string of hex bytes
    """
    return ' '.join(binascii.hexlify(ch) for ch in reply)


def reply2hex_pic(reply):
    """
    Parse the replied unicode when taking pictures
    chars 6, 7, 8 are hex bytes for n_bytes
    chars 9 and 10 are hex bytes for n_packets
    :param reply: unicode
    :return: int (number of bytes), int (number of packets)
    """
    if ord(reply[5]) != 0:
        return False
    n_bytes = int(''.join(binascii.hexlify(ch) for ch in reply[6:9]), 16)
    n_packets = int(''.join(binascii.hexlify(ch) for ch in reply[9:11]), 16)
    return n_bytes, n_packets


def reply2list(reply):
    """
    Parse the replied unicode to a list of integers, as the command style
    :param reply:
    :return: int[]
    """
    reply_list = []
    for c in reply:
        reply_list.append(ord(c))
    return reply_list


def save_img(photo, fn):
    """
    Save the image
    :param photo:
    :param fn:
    :return:
    """
    try:
        f = open(fn, 'w')
        photo_data = ''.join(photo)
        f.write(photo_data)
        f.close()
    except:
        pass


class CameraSerial(serial.Serial):

    def config_connection(self, cmd, baud):
        """
        Configure the camera settings
        :param cmd: command
        :param baud: new baudrate
        :return:
        """
        self.write(cmd)
        reply_hex = reply2hex(self.read(size=13))
        self.baudrate = baud
        return reply_hex

    def send_cmd(self, cmd, rlist=False):
        """
        Send the command to the camera
        :param cmd: int[], list of command
        :param rlist: boolean, return list or not
        :return: reply from the camera
        """
        self.write(cmd)
        reply = self.read(size=13)
        reply_hex = reply2hex(reply)
        if rlist:
            reply_list = reply2list(reply)
            return reply_hex, reply_list
        return reply_hex

    def take_picture(self, cmd):
        """
        Let the camera to take a picture
        :param cmd:
        :return:
        """
        self.write(cmd)
        reply = self.read(size=13)
        reply_hex = reply2hex(reply)
        n_bytes, n_packets = reply2hex_pic(reply)
        return reply_hex, n_bytes, n_packets

    def upload_img(self, fn, n_bytes, n_packets, packet_size):
        """
        Upload a picture to host
        :param fn: filename of uploaded image
        :param n_bytes: number of bytes of the image
        :param n_packets: number of packets of the image
        :param packet_size: number of bytes of a packet
        :return: unicode of the entire img
        """
        n_packets_list = int2hexList(n_packets)
        photo = []
        for idx in range(1, n_packets + 1):
            idx_packet = int2hexList(idx)
            params = [0x01] + idx_packet + n_packets_list + [PARAM_EMPTY]
            idx_cmd = format_cmd(CMD_UPLOAD, params)
            try:
                self.write(idx_cmd)
                if idx == n_packets:
                    last_bytes = n_bytes % packet_size
                    reply = self.read(size=13 + last_bytes)
                    photo += reply[11:11+last_bytes]
                else:
                    reply = self.read(size=13 + packet_size)
                    photo += reply[11:11+packet_size]
            except ValueError:
                print idx_cmd
        save_img(photo=photo, fn=fn)

    def reset(self):
        cmd = format_cmd(CMD_CONFIG, [baudrate_dict[115200], 0x00, packet_dict[512], 0, 0, 0])
        self.config_connection(cmd, 115200)


# main
# Initial configuration command
def main():
    """
    Please read the main function, some information of the Chinese datasheet is being translated here
    :return:
    """
    # Default baud rate of the camera is 115200, user can choose packet size from the dict above
    baud = 230400
    packet_size = 1024

    # Configuration command
    # Params = [baudrate, ID, packet_size, 0, 0, 0]
    config_cmd = format_cmd(CMD_CONFIG, [baudrate_dict[baud], 0x00, packet_dict[packet_size], 0, 0, 0])

    # Get configuration command
    getinfo_cmd = format_cmd(CMD_GETVERSION, [PARAM_EMPTY]*6)

    cs = CameraSerial(PORT, baudrate=BAUD, timeout=TIMEOUT)

    # Configure the connection
    reply = cs.config_connection(config_cmd, baud)
    print reply

    # Read the configuration
    reply = cs.send_cmd(getinfo_cmd)
    print reply

    # autofocus
    # cmd is CMD_FOCUS
    # Params = [auto(0x01)/read(0x02)/manual(0x03),
    #           [0-750 focus value if manual] (convert the int to two hex bytes please),
    #           0,
    #           0,
    #           0]
    autofocus_cmd = format_cmd(CMD_FOCUS, [0x01, PARAM_EMPTY, PARAM_EMPTY, PARAM_EMPTY, PARAM_EMPTY, PARAM_EMPTY])
    reply = cs.send_cmd(autofocus_cmd)
    print reply

    # take test picture
    # cmd is CMD_TAKEPIC
    # Params = [resolution,
    #           binary/color(2nd digit in hex, 0 is color, 1 is black)
    #           and precision(1st digit in hex, 1(high) to 4 (low)),
    #           picture format (1=JPG, 2=RGB565, 3=YUV422, 4=8bit grayscale),
    #           exposure(0 is auto, 128-143 are 16 exposure levels),
    #           0,
    #           0]
    takeimg_cmd = format_cmd(CMD_TAKEPIC, [0x03, 0x02, 0x01, 0x00, 0x00, 0x00])
    reply, n_bytes, n_packets = cs.take_picture(takeimg_cmd)
    print reply, n_bytes, n_packets

    cs.upload_img(fn="photo.jpg", n_bytes=n_bytes, n_packets=n_packets, packet_size=packet_size)

    cs.reset()
    cs.close()

if __name__ == "__main__":
    main()

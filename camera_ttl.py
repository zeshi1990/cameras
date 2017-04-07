import binascii
import serial

# Default settings, these could be changed
BAUD = 115200
PORT = "/dev/tty.wchusbserial1410"
TIMEOUT = 1.2

# Default command code
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

# No configuration
PARAM_EMPTY = 0x00

# Baudrate configuration dictionary
baudrate_dict = {9600: 0x01, 19200: 0x02,
                 38400: 0x03, 57600: 0x04,
                 115200: 0x05, 230400: 0x06,
                 460800: 0x07, 921600: 0x08}

# Packet size configuration dictionary
packet_dict = {256: 0x01, 512: 0x02,
               1024:0x03, 2048: 0x04}


def int2hexList(val):
    hex_str = "{0:#0{1}x}".format(val, 6)[2:]
    return [int(hex_str[:2], 16), int(hex_str[2:], 16)]


def format_cmd_hex(cmd, params):
    """
    Deprecated, this won't work in Python
    :param cmd: a hex for command
    :param params: 6 hexes for command parameters
    :return: send command string
    """

    send_command = "\x7E\x00\x08\x00" + chr(cmd) + ''.join(chr(param) for param in params)
    checksum = sum(bytearray(send_command[1:]))
    checksum %= 256
    send_command += chr(checksum) + chr(0xE7)
    send_command_hex = ' '.join(binascii.hexlify(ch) for ch in send_command)
    return send_command_hex


def format_cmd(cmd, params):
    """
    Format the commands into a list of integers
    :param cmd:
    :param params:
    :return: return a list of commands
    """

    # Header are always \x7E\x00\x08\x00
    # Tail is checksum + \xE7
    send_command = "\x7E\x00\x08\x00" + chr(cmd) + ''.join(chr(param) for param in params)

    checksum = sum(bytearray(send_command[1:]))
    checksum %= 256

    send_command_list = []
    for c in send_command:
        send_command_list.append(ord(c))
    send_command_list += [checksum, int('E7', 16)]
    return send_command_list

def reply2hex(reply):
    return ' '.join(binascii.hexlify(ch) for ch in reply)


def reply2hex_pic(reply):
    if ord(reply[5]) != 0:
        return False
    byte_length = int(''.join(binascii.hexlify(ch) for ch in reply[6:9]), 16)
    package_length = int(''.join(binascii.hexlify(ch) for ch in reply[9:11]), 16)
    return byte_length, package_length


def reply2list(reply):
    reply_list = []
    for c in reply:
        reply_list.append(ord(c))
    return reply_list


def send_cmd(s, cmd, list=False):
    s.write(cmd)
    reply = s.read(size=13)
    reply_hex = reply2hex(reply)
    if list:
        reply_list = reply2list(reply)
        return reply_hex, reply_list
    return reply_hex


def take_picture(s, cmd):
    s.write(cmd)
    reply = s.read(size=13)
    reply_hex = reply2hex(reply)
    n_bytes, n_packets = reply2hex_pic(reply)
    return reply_hex, n_bytes, n_packets


def upload_img(s, n_bytes, n_packets, packet_size):
    n_packets_list = int2hexList(n_packets)
    photo = []
    for idx in range(1, n_packets + 1):
        idx_packet = int2hexList(idx)
        params = [0x01] + idx_packet + n_packets_list + [PARAM_EMPTY]
        idx_cmd = format_cmd(CMD_UPLOAD, params)
        try:
            s.write(idx_cmd)
            if idx == n_packets:
                last_bytes = n_bytes % packet_size
                reply = s.read(size=13 + last_bytes)
                photo += reply[11:11+last_bytes]
            else:
                reply = s.read(size = 13 + packet_size)
                photo += reply[11:11+packet_size]
        except ValueError:
            print idx_cmd
    return photo


def config_connection(s, cmd, baud):
    s.write(cmd)
    reply_hex = reply2hex(s.read(size=13))
    s.baudrate = baud
    return reply_hex

# Initial configuration command
baud = 115200
packet_size = 512

# Configuration command
# Params = [baudrate, ID, packet_size, 0, 0, 0]
config_cmd = format_cmd(CMD_CONFIG, [baudrate_dict[baud], 0x00, packet_dict[packet_size], 0, 0, 0])

# Get configuration command
getInfo_cmd = format_cmd(CMD_GETVERSION, [PARAM_EMPTY]*6)


s = serial.Serial(PORT, baudrate=BAUD, timeout=TIMEOUT)

# Configure the connection
reply = config_connection(s, config_cmd, baud)
print reply

# Read the configuration
reply = send_cmd(s, getInfo_cmd)
print reply

# autofocus
# Params = [auto(0x01)/read(0x02)/manual(0x03), [0-750 if manual] (two bytes), 0, 0, 0]
autofocus_cmd = format_cmd(CMD_FOCUS, [0x01, PARAM_EMPTY, PARAM_EMPTY, PARAM_EMPTY, PARAM_EMPTY, PARAM_EMPTY])
reply = send_cmd(s, autofocus_cmd)
print reply

# take test picture
# Params = []
takeimg_cmd = format_cmd(CMD_TAKEPIC, [0x03, 0x02, 0x01, 0x00, 0x00, 0x00])
takeimg_cmd_hex = format_cmd_hex(CMD_TAKEPIC, [0x06, 0x11, 0x01, 0x86, 0x00, 0x00])
reply, n_bytes, n_packets = take_picture(s, takeimg_cmd)
print reply, n_bytes, n_packets

photo = upload_img(s, n_bytes=n_bytes, n_packets=n_packets, packet_size=packet_size)

f = open("photo.jpg", "w")
photodata = ''.join(photo)
f.write(photodata)
f.close()
import os
import sys
import time
import select
import spidev
import threading

is_on_raspberry_pi = False
with open('/etc/os-release') as os_version_file:
    is_on_raspberry_pi = 'raspbian' in os_version_file.read().lower()

spi = None
if is_on_raspberry_pi:
    spi = spidev.SpiDev(0, 0) # rasp
    print("I'm on Raspberry Pi!")
    os.system("echo 16 > /sys/class/gpio/export")
    os.system("echo in > /sys/class/gpio/gpio16/direction")
    os.system("echo rising > /sys/class/gpio/gpio16/edge")
    print("GPIO init done")
else:
    spi = spidev.SpiDev(1, 0) # lichee
    print("I'm on custom board!")

spi.max_speed_hz = 2000000

keyboard_opened_device_dict = {}
mouse_opened_device_dict = {}
gamepad_opened_device_dict = {}

gpio_file = open("/sys/class/gpio/gpio16/value", 'rb')

epoll = select.epoll()
epoll.register(gpio_file, select.EPOLLET)

"""
def send kb

def send mouse

def send js

read data first, if exception, skip it
"""

"""
https://elixir.bootlin.com/linux/latest/source/include/uapi/linux/input-event-codes.h#L38

xbox gamepad:
EVENT TYPE: EV_ABS
dpad: ABS_HAT0X ABS_HAT1X
buttons: https://elixir.bootlin.com/linux/latest/source/include/uapi/linux/input-event-codes.h#L385
sticks: ABS_X, ABS_Y, ABS_RX, ABS_RY
"""

EV_KEY = 0x01
EV_REL = 0x02
EV_ABS = 0x03

SPI_MOSI_MSG_KEYBOARD_EVENT = 1
SPI_MOSI_MSG_MOUSE_EVENT = 2
SPI_MOSI_MSG_GAMEPAD_EVENT = 3
SPI_MOSI_MSG_REQ_ACK = 4

SPI_MOSI_MAGIC = 0xde
SPI_MISO_MAGIC = 0xcd

def make_spi_msg_ack():
    return [SPI_MOSI_MAGIC, 0, SPI_MOSI_MSG_REQ_ACK] + [0]*29

keyboard_spi_msg_header = [SPI_MOSI_MAGIC, 0, SPI_MOSI_MSG_KEYBOARD_EVENT, 0]

def raw_input_event_worker():
    print("raw_input_event_parser_thread started")
    to_delete = []
    while 1:
        for key in list(keyboard_opened_device_dict):
            try:
                data = keyboard_opened_device_dict[key][0].read(16)
            except OSError:
                keyboard_opened_device_dict[key][0].close()
                del keyboard_opened_device_dict[key]
                print("device disappeared:", key)
            if data is None:
                continue
            data = list(data[8:])
            if data[0] == EV_KEY:
                to_transfer = keyboard_spi_msg_header + data + [0]*20
                to_transfer[3] = keyboard_opened_device_dict[key][1]
                spi.xfer(to_transfer)
                print(time.time(), 'sent')
                # print(key)
                # print(to_transfer)
                # print('----')
        events = epoll.poll(timeout=0)
        for df, event_type in events:
            if 0x8 & event_type:
                slave_result = None
                for x in range(3):
                    slave_result = spi.xfer(make_spi_msg_ack())
                print(slave_result)
                if slave_result[0] == SPI_MISO_MAGIC:
                    print("good!")

raw_input_event_parser_thread = threading.Thread(target=raw_input_event_worker, daemon=True)
raw_input_event_parser_thread.start()

input_device_path = '/dev/input/by-path/'

while 1:
    try:
        device_file_list = os.listdir(input_device_path)
    except Exception as e:
        print('list input device exception:', e)
        time.sleep(0.75)
        continue
    mouse_list = [os.path.join(input_device_path, x) for x in device_file_list if 'event-mouse' in x]
    keyboard_list = [os.path.join(input_device_path, x) for x in device_file_list if 'event-kbd' in x]
    gamepad_list = [os.path.join(input_device_path, x) for x in device_file_list if 'event-joystick' in x]
    # print(mouse_list)
    # print(keyboard_list)

    for item in keyboard_list:
        if item not in keyboard_opened_device_dict:
            try:
                this_file = open(item, "rb")
                os.set_blocking(this_file.fileno(), False)
                kb_index = 0
                try:
                    kb_index = sum([int(x) for x in item.split(':')[1].split('.')][:2])
                except:
                    pass
                keyboard_opened_device_dict[item] = (this_file, kb_index)
                print("opened keyboard", keyboard_opened_device_dict[item][1], ':' , item)
            except Exception as e:
                print("keyboard open exception:", e)
                continue

    time.sleep(0.75)
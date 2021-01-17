import wget
from os import path
import esptool
import ssl
import serial
from time import sleep
from getpass import getpass

FIRMWARE = 'esp8266-20200911-v1.13.bin'

def ensure_firmware_file():
    if path.exists(FIRMWARE):
        return
    print(f'{FIRMWARE} not found, try to download...')
    ssl._create_default_https_context = ssl._create_unverified_context
    filename = wget.download(f'https://micropython.org/resources/firmware/{FIRMWARE}')
    if not path.exists('esp8266-20200911-v1.13.bin'):
        raise Exception('Could not download firmware.')
    print('ok')

def burn_firmware(term_port):
    print('Erase Flash...')
    esptool.main(['--port', term_port, 'erase_flash'])
    print('Write Flash...')
    esptool.main(['--port', term_port, 'write_flash', '--flash_size=detect', '0', 'esp8266-20200911-v1.13.bin'])
    print('ok')
    sleep(2)

def copy_boot_file(term_port, baudrate, wlan_ssid, wlan_pwd, host_name):
    print('Copy boot.py...')
    with open('boot.py_template', 'r') as f:
        boot_py = f.readlines()
    def replace(line):
        line = line.replace('$wlan_ssid', wlan_ssid)
        line = line.replace('$wlan_pwd', wlan_pwd)
        line = line.replace('$host_name', host_name)
        return line
    boot_py = [replace(line) for line in boot_py]
    ser = serial.Serial(port=term_port, baudrate=baudrate, timeout=1)
    ser.write(
'''\5def reader():
    import sys
    f = open("boot.py", "w")
    for line in sys.stdin:
        if line.startswith("<<EOF>>"):
            break
        f.write(line)
    f.close()
reader()
\4'''.encode())
    sleep(2)
    for line in boot_py:
        ser.write(line.encode())
        sleep(0.01)
    ser.write('<<EOF>>\r\n'.encode())
    for line in ser.readlines():
        pass
    ser.close()

def main():
    try:
        wlan_ssid = input('Input WLAN SSID: ')
        while True:
            wlan_pwd = getpass('Input WLAN password: ')
            wlan_pwd2 = getpass('Confirm WLAN password: ')
            if wlan_pwd == wlan_pwd2:
                break
            print('Passwords do not match. Try again!')
        term_port = input('Input usb terminal device: ')
        while True:
            while True:
                note = input('Input musical note (e.g. C1 for lower C), or empty line to quit: ').upper()
                if note == '':
                    break
                if len(note) != 2 or note[0] not in ('A', 'B', 'C', 'D', 'E', 'F') or note[1] not in ('1', '2'):
                    print('Please use a char(A, B, C, D, E, F) plus a digit (1 or 2). 1 for the lower and 2 for the higher octave.')
                    continue
                else:
                    break
            if note == '':
                break
            input('Insert ESP module and turn on programmer, then press RETURN.')
            host_name = 'OGONO_' + note
            ensure_firmware_file()
            burn_firmware(term_port)
            copy_boot_file(term_port, 74880, wlan_ssid, wlan_pwd, host_name)
            print('Done')
            print('You can press RST on the programmer to test the module, if you want to.')
            input('Then turn off programmer and remove module, then press RETURN.')
            print()
        print('Bye')
    except Exception as e:
        print(f'{type(e).__name__}: {str(e)}')

if __name__ == '__main__':
    main()
# -*- coding: utf-8 -*-
import sys
import socket
from psutils import out
from psutils import log
from psutils import recv
from psutils import send
from psutils import image2bytes
from psutils import bytes2str

import pyautogui
#scrot

def getScreen() -> str:
    #m1 = pyautogui.screenshot(region=(0,0, 1280, 720))
    m1 = pyautogui.screenshot()
    ma = image2bytes(m1)
    #writeFileBytes("test.png", ma)
    resstr = bytes2str(ma)
    return resstr

'''
def getScreen() -> str:
    return "1111_231_231231231231231231231211_231_23123123123123123123123123v233123v2311_2 31_23123123123123123123123123v2311_231_23123123123123123123123123v23_211_231_23123123123123123123123123v2331_23123123123123123123123123v23"
'''

if __name__ == "__main__":
    '''
    > python photo.py ip port passwd
                0     1   2     3
    '''
    if(len(sys.argv) != 4):
        out("Sytax error. Check README.md: https://github.com/The220th/photoshark")

    connection = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    IP = sys.argv[1]
    PORT = int(sys.argv[2])
    PASSWD = sys.argv[3]
    connection.connect((IP, PORT))
    send(connection, "SHARK")

    log("sharked")
    while(True):
        command = recv(connection)
        if(command == "n"):
            break
        send(connection, getScreen())
    
    connection.close()
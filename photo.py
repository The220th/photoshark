# -*- coding: utf-8 -*-
import sys
import socket
from psutils import out
from psutils import log
from psutils import recv
from psutils import send
from psutils import str2bytes
from psutils import writeFileBytes

def saveScreenshot(s : str):
    ma = str2bytes(s)
    writeFileBytes("test.png", ma)

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
    send(connection, "PHOTO")

    while(True):
        print("Input command: \n> ", end = "")
        u = input()
        if(not (u == "s" or u == "n")):
            out("only \"s\" or \"n\". Check README.md: https://github.com/The220th/photoshark")
            continue
        send(connection, u)
        if(u == "n"):
            break
        pic = recv(connection)
        saveScreenshot(pic)
        log(f"get pic: {pic}")
    
    connection.close()
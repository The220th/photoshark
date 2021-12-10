# -*- coding: utf-8 -*-
import sys
import socket
from psutils import out
from psutils import log
from psutils import recv
from psutils import send

'''
Протокол:
Сервер инициализируется
Клиекты делают регистрацию: отсылают строку "PHOTO" или "SHARK"
while:
    photo отылает "s"
    Сервер пересылает "s" shark
    shark делает скрин и отсылает серверу
    Сервер пересылает скрин photo
    photo сохраняет скрин
'''

def initPS(connection, address):
    global photo
    global shark
    global photoAddr
    global sharkAddr
    log(f"Connection: {connection}, address: {address}")
    regMsg = recv(connection)
    log(f"Get reg msg: {regMsg}")
    if(regMsg == "PHOTO"):
        photo = connection
        photoAddr = address
        log("photo inited")
    elif(regMsg == "SHARK"):
        shark = connection
        sharkAddr = address
        log("shark inited")
    else:
        log("It is no SHARK or PHOTO registration")
        exit()

if __name__ == "__main__":
    '''
    > python psserver.py ip port
                 0       1   2
    '''
    photo = None
    shark = None
    photoAddr = None
    sharkAddr = None

    if(len(sys.argv) != 3):
        out("Sytax error. Check README.md: https://github.com/The220th/photoshark")
    
    listener = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    listener.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    #IP = socket.gethostbyname(socket.gethostname())
    IP = sys.argv[1]
    PORT = int(sys.argv[2])
    listener.bind((IP, PORT))
    listener.listen()
    #listener.setblocking(False)
    c, a = listener.accept()
    initPS(c, a)
    c, a = listener.accept()
    initPS(c, a)
    while(True):
        photoReg = recv(photo)
        log(f"photo sent: {photoReg}")
        if(photoReg == "n"):
            send(shark, photoReg)
            break
        send(shark, photoReg)
        sharkScreen = recv(shark)
        #log(f"Photo sent {sharkScreen}")
        send(photo, sharkScreen)
    photo.close()
    shark.close()
# -*- coding: utf-8 -*-

import sys
import os
import io
import datetime
import time
from threading import Thread

import socket
import select

import pyautogui

def pout(S: str, endl: bool = True):
    if(endl == False):
        print(S, end="")
    else:
        print(S)

def plog(s: str):
    time_str = datetime.datetime.now().strftime("[%y.%m.%d %H:%M:%S.%f]")
    pout(f"{time_str} {s}")

def perr(err: str):
    print(f"\n===============\n\t{err}\n===============\n")

def int_to_bytes(a: int) -> bytes:
    if(a < 0 or a > 4294967295):
        perr(f"int_to_bytes: number {a} more than 2**32-1 or less zero. ")
    return a.to_bytes(4, "big")
    
def bytes_to_int(bs: bytes) -> int:
    res = int.from_bytes(bs, "big")
    if(res < 0 or res > 4294967295):
        perr(f"bytes_to_int: number {res} more than 2**32-1 or less zero from bytes: \"{bs}\". ")
    return res

def utf8_to_bytes(s: str) -> bytes:
    return s.encode("utf-8")

def bytes_to_utf8(bs: bytes) -> str:
    return str(bs, "utf-8")

def image_to_bytes(image: "pyautogui image") -> bytes:
    img_byte_arr = io.BytesIO()
    image.save(img_byte_arr, format='PNG')
    img_byte_arr = img_byte_arr.getvalue()
    return img_byte_arr

def write2File_str(fileName : str, s : str) -> None:
    with open(fileName, 'w', encoding="utf-8") as temp:
        temp.write(s)

def write2file_bytes(fileName : str, bs : bytes) -> None:
    with open(fileName, 'wb') as temp:
        temp.write(bs)

def send_msg(conn, bs: bytes):
    bs_len = len(bs)
    plog(f"send_msg: Sending {bs_len} bytes... ")
    bs_len = int_to_bytes(bs_len)
    bs_to_send = bs_len + bs
    buff = conn.sendall(bs_to_send)
    if(buff != None):
        perr(f"send_msg: cannot send {bs_len} bytes")

def recv_msg(conn) -> bytes:
    plog(f"recv_msg: Recieving size of msg")
    BUFF_SIZE = 1024
    msg_size_b = conn.recv(4)
    msg_size = bytes_to_int(msg_size_b)
    plog(f"recv_msg: Size of msg is {msg_size} bytes")
    i = 0
    res = bytes()
    #time.sleep(1)
    while(i < msg_size):
        #if(i+BUFF_SIZE < msg_size):
            res += conn.recv(BUFF_SIZE)
            i += BUFF_SIZE
        #else:
        #    to_rcv = msg_size - i
        #    res += conn.recv(to_rcv)
        #    i += to_rcv
    res = res[:msg_size]
    plog(f"recv_msg: Recieved {len(res)} ({i}) bytes")
    return res


# port
#  0
def main_server(argv: list):
    port = int(argv[0])
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.bind(("", port))
    sock.listen(5)

    fds = {}
    while True:
        readable, trash2, trash3 = select.select([sock] + list(fds.values()), [], [])
        for fd_i in readable:
            if(fd_i == sock):
                conn, info = sock.accept()
                conn.setblocking(0)

                select.select([conn], [], [], 0)
                bs = recv_msg(conn)
                hello_msg = bytes_to_utf8(bs)
                if(hello_msg == "i_am_photo"):
                    fds["photo"] = conn
                elif(hello_msg == "i_am_shark"):
                    fds["shark"] = conn
                elif(hello_msg == "i_am_show"):
                    fds["show"] = conn
                else:
                    perr("main_server: unknown hello message: \"hello_msg\"")

            if("shark" in fds and fd_i == fds["shark"]):
                bs = recv_msg(fd_i)
                msg = bytes_to_utf8(bs)
                if(msg == "take_photo"):
                    send_msg(fds["photo"], utf8_to_bytes("take_photo"))
                    
                    select.select([fds["photo"]], [], [])
                    image = recv_msg(fds["photo"])
                    
                    send_msg(fd_i, image)



# ip port
# 0   1
def main_photo(argv: list):
    ip = argv[0]
    port = int(argv[1])
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.connect((ip, port))
    sock.setblocking(0)
    
    hello_msg = utf8_to_bytes("i_am_photo")
    send_msg(sock, hello_msg)

    while(True):
        select.select([sock], [], [])
        bs = recv_msg(sock)
        bs_str = bytes_to_utf8(bs)
        plog(f"main_photo: get msg from server: \"{bs_str}\". ")
        if(bs_str == "take_photo"):
            bs = image_to_bytes(pyautogui.screenshot())
            send_msg(sock, bs)
        time.sleep(1)


# ip port
# 0   1
def main_shark(argv: list):
    ip = argv[0]
    port = int(argv[1])
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.connect((ip, port))
    sock.setblocking(0)

    hello_msg = utf8_to_bytes("i_am_shark")
    send_msg(sock, hello_msg)

    pout("What do you want? \n\tPress Enter to get screen from photo \nor \n\tType message and press Enter to send this message to show. ")
    gi = 0
    while(True):
        print("> ", end="")
        user_input = input()
        if(user_input == ""):
            send_msg(sock, utf8_to_bytes("take_photo") )

            select.select([sock], [], [])
            bs = recv_msg(sock)
            screen_file_name = f"screen{gi}.png"
            write2file_bytes(screen_file_name, bs)
            gi += 1
            pout(f"Saved screenshot to \"{screen_file_name}\"\n")


            

def main_show(argv: list):
    pass

if __name__ == "__main__":
    argc = len(sys.argv)
    if(argc < 2):
        pout("Syntax error. Expected: \"> python photoshark.py {server, photo, shark, show} ...\"")
    
    whoiam = sys.argv[1]
    if(whoiam == "server"):
        main_server(sys.argv[2:])
    elif(whoiam == "photo"):
        main_photo(sys.argv[2:])
    elif(whoiam == "shark"):
        main_shark(sys.argv[2:])
    elif(whoiam == "show"):
        main_show(sys.argv[2:])
    else:
        pout("Syntax error. Expected: \"> python photoshark.py {server, photo, shark, show} ...\"")
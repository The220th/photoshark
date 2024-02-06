# -*- coding: utf-8 -*-

import sys
import os
import io
import datetime
import time
import base64
import hashlib

import socket
import select

# pip install --upgrade pip
# pip3 install pyautogui Pillow cryptography  # for photo and shark
#
# python photoshark.py server {port}
# python photoshark.py shark {ip} {port} [{cipher_key}]
# python photoshark.py photo {ip} {port} [{cipher_key}]
# python photoshark.py show {ip} {port}

IF_DEBUG_MSG = True

def pout(S: str, endl: bool = True):
    if(endl == False):
        print(S, end="")
    else:
        print(S)

def plog(s: str):
    if(IF_DEBUG_MSG == False):
        return
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

def calc_bytes_hash(bs: bytes) -> "4 bytes":
    #a = hash(bs)
    a = 7
    for b_i in bs:
        a = (31*a + b_i) % 4294967295
    a = a % 4294967295
    return int_to_bytes(a)

def pand(bs: bytes, N: int) -> bytes:
    n = len(bs)
    if(n % N != 0):
        res = bs + b'\x00'*(N - n%N)
    else:
        res = bs
    return res

def print_bytes(bs: bytes):
    res = ""
    for i in bs:
        res += f"{i}_"
    res = res[:-1]
    #return res
    print(f"\n{res}")

BUFF_SIZE = 1024

def send_msg(conn, bs: bytes):
    # print_bytes(bs)
    bs_len = len(bs)
    plog(f"send_msg: Sending {bs_len} bytes... ")
    info_1 = int_to_bytes(bs_len) # кол-во байт в bs
    bs_pand = pand(bs, BUFF_SIZE)
    page_num = len(bs_pand)//BUFF_SIZE
    info_2 = int_to_bytes(page_num) # кол-во страниц bs_pand
    info_3 = calc_bytes_hash(bs) # хэш bs
    plog(f"send_msg: (1)bs_len={bs_len}, (2)page_nums={page_num}, (3)bs_hash=\"{info_3}\"")
    info_msg = pand(info_1 + info_2 + info_3, BUFF_SIZE)
    plog(f"send_msg: info block formed: \"{info_msg[:12]}...\"")
    # print_bytes(info_msg)
    buff = conn.send(info_msg)
    if(buff != BUFF_SIZE):
        perr(f"send_msg cannot send {BUFF_SIZE} bytes, only {buff}")
    for i in range(page_num):
        # print_bytes(bs_pand[i*BUFF_SIZE:(i+1)*BUFF_SIZE])
        buff = conn.send(bs_pand[i*BUFF_SIZE:(i+1)*BUFF_SIZE])
        if(buff != BUFF_SIZE):
            perr(f"send_msg cannot send {BUFF_SIZE} bytes, only {buff}")
    plog(f"send_msg: sended! ")

def recv_msg(conn) -> bytes:
    plog(f"recv_msg: recieving info block")
    info_block = conn.recv(BUFF_SIZE, socket.MSG_WAITALL)
    # print_bytes(info_block)
    if(len(info_block) != BUFF_SIZE):
        perr(f"recv_msg: cannot get {BUFF_SIZE} bytes. Get only {len(info_block)}! ")
    plog(f"recv_msg: info block recieved: \"{info_block[:12]}...\"")
    info_1 = bytes_to_int( info_block[:4] ) # кол-во байт в bs
    info_2 = bytes_to_int( info_block[4:8] ) # кол-во страниц bs_pand
    info_3 = info_block[8:12] # хэш bs
    plog(f"recv_msg: (1)bs_len={info_1}, (2)page_nums={info_2}, (3)bs_hash=\"{info_3}\"")
    res = bytes()
    for i in range(info_2):
        buff = conn.recv(BUFF_SIZE, socket.MSG_WAITALL)
        # print_bytes(buff)
        if(len(buff) != BUFF_SIZE):
            perr(f"recv_msg: cannot get {BUFF_SIZE} bytes. Get only {len(buff)}! ")
        res += buff
    res = res[:info_1]
    # print_bytes(res)
    res_hash = calc_bytes_hash(res)
    if(len(res_hash) != len(info_3) or False in [res_hash[i] == info_3[i] for i in range(len(res_hash))]):
        perr(f"recv_msg: hashes do not match: info_hash=\"{info_3}\" and res_hash=\"{res_hash}\"! ")
    plog("recv_msg: recieved! ")
    return res



SCREEN_CIPHER = None

class PycaFernet:
    def __init__(self, password: str):
        self.iv = None
        self.key = None
        self.cipher = None

        from cryptography.fernet import Fernet
        from cryptography.hazmat.primitives import hashes, padding
        from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
        from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes

        # key_len = len(Fernet.generate_key())
        pwd = password.encode("utf-8")
        salt = hashlib.sha256(pwd).digest()[:16]
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,  # key_len
            salt=salt,
            iterations=480000
        )
        # self.key = base64.urlsafe_b64encode(kdf.derive(pwd))
        self.key = kdf.derive(pwd)
        self.key = base64.urlsafe_b64encode(self.key)

        print(self.key)
        self.cipher = Fernet(self.key)

    def encrypt(self, bs: bytes) -> bytes or None:
            return self.cipher.encrypt(bs)

    def decrypt(self, ct: bytes) -> bytes or None:
            return self.cipher.decrypt(ct)

def form_screen_bytes(bs: bytes) -> bytes:
    if(SCREEN_CIPHER == None):
        return bs
    else:
        plog(f"form_screen_bytes: encrypting screen")
        return SCREEN_CIPHER.encrypt(bs)

def deform_screen_bytes(bs: bytes) -> bytes:
    if(SCREEN_CIPHER == None):
        return bs
    else:
        plog(f"deform_screen_bytes: decrypting screen")
        res = SCREEN_CIPHER.decrypt(bs)
        return res

# port
#  0
def main_server(argv: list):
    if(len(argv) != 1):
        perr("Sytax error! Expected: \"> python photoshark.py server {port}\". ")
        exit()
    try:
        port = int(argv[0])
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.bind(("", port))
        sock.listen(5)

        fds = {}
        plog("Server started! ")
        while True:
            pout("")
            readable, trash2, trash3 = select.select([sock] + list(fds.values()), [], [])
            for fd_i in readable:
                if(fd_i == sock):
                    plog("main_server: new connection")
                    conn, info = sock.accept()
                    #conn.setblocking(0)

                    #select.select([conn], [], [], 0)
                    bs = recv_msg(conn)
                    hello_msg = bytes_to_utf8(bs)
                    plog(f"main_server: hello message: \"{hello_msg}\". ")
                    if(hello_msg == "i_am_photo"):
                        fds["photo"] = conn
                    elif(hello_msg == "i_am_shark"):
                        fds["shark"] = conn
                    elif(hello_msg == "i_am_show"):
                        fds["show"] = conn
                    else:
                        perr("main_server: unknown hello message: \"hello_msg\"")

                if("shark" in fds and fd_i == fds["shark"]):
                    plog("main_server: shark awoken. ")
                    bs = recv_msg(fd_i)
                    msg = bytes_to_utf8(bs)
                    plog(f"main_server: shark says: \"{msg}\". ")
                    if(msg == "take_photo"):
                        if("photo" not in fds):
                            plog(f"main_server: photo is still out... ")
                            plog(f"main_server: sending trash to shark. ")
                            send_msg(fd_i, utf8_to_bytes("photo is still out. Wait pls. "))
                        else:
                            plog(f"main_server: sending msg \"take_photo\" to photo. ")
                            send_msg(fds["photo"], utf8_to_bytes("take_photo"))

                            plog(f"main_server: getting screen from photo. ")
                            #select.select([fds["photo"]], [], [])
                            image = recv_msg(fds["photo"])
                            
                            plog(f"main_server: sending screen to shark. ")
                            send_msg(fd_i, image)
                    elif(len(msg) > 5 and msg[:5] == "show:"):
                        if("show" not in fds):
                            plog(f"main_server: show is still out... ")
                            send_msg(fd_i, utf8_to_bytes("no show yet. "))
                        else:
                            msg4show = msg[5:]
                            plog(f"main_server: sending msg \"{msg4show}\" to show. ")
                            send_msg(fds["show"], utf8_to_bytes(msg4show))

                            plog(f"main_server: getting ok msg from show. ")
                            #select.select([fds["show"]], [], [])
                            bs = recv_msg(fds["show"])
                            msg_from_show = bytes_to_utf8(bs)
                            plog(f"main_server: getted msg from show: \"{msg_from_show}\"")
                            if(msg_from_show == "OK"):
                                plog(f"main_server: send ok msg to shark. ")
                                send_msg(fd_i, utf8_to_bytes("show got the message. "))
                            else:
                                plog(f"main_server: send err msg to shark. ")
                                send_msg(fd_i, utf8_to_bytes("problem with sending a message to show. Try again. "))
                                
                    else:
                        perr(f"main_server: get trash from shark")
    except Exception as eerrrrr:
        print(eerrrrr)
        plog(f"Some bullshit happened. Restarting... ")
        time.sleep(5)
        main_server(argv)
    except KeyboardInterrupt:
        plog("main_server: Shutdowning")
        sock.close()



# ip port [cipher_key]
# 0   1         2
def main_photo(argv: list):
    import pyautogui
    if(len(argv) < 2 or len(argv) > 3):
        perr("Sytax error! Expected: \"> python photoshark.py photo {ip} {port} [{cipher_key}]\". ")
        exit()
    if(len(argv) == 3):
        global SCREEN_CIPHER
        SCREEN_CIPHER = PycaFernet(argv[2])
    try:
        plog("photo starting")
        ip = argv[0]
        port = int(argv[1])
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.connect((ip, port))
        #sock.setblocking(0)
        
        plog("main_photo: sending hello msg: \"i_am_photo\"")
        hello_msg = utf8_to_bytes("i_am_photo")
        send_msg(sock, hello_msg)
        shit_count = 0
        while(True):
            #select.select([sock], [], [])
            bs = recv_msg(sock)
            bs_str = bytes_to_utf8(bs)
            plog(f"main_photo: get msg from server: \"{bs_str}\". ")
            if(bs_str == ""):
                plog(f"({shit_count}) Server down?")
                time.sleep(3)
                shit_count += 1
                if(shit_count > 5):
                    plog("Server downed. Reconnecting...")
                    raise "bullshit happened"
            if(bs_str == "take_photo"):
                bs = image_to_bytes(pyautogui.screenshot())
                bs = form_screen_bytes(bs)
                send_msg(sock, bs)
            #time.sleep(1)
    except Exception as eerrrrr:
        print(eerrrrr)
        plog(f"Some bullshit happened. Restarting... ")
        time.sleep(5)
        main_photo(argv)


# ip port [cipher_key]
# 0   1        2
def main_shark(argv: list):
    import pyautogui
    if(len(argv) < 2 or len(argv) > 3):
        perr("Sytax error! Expected: \"> python photoshark.py shark {ip} {port} [{cipher_key}]\". ")
        exit()
    if(len(argv) == 3):
        global SCREEN_CIPHER
        SCREEN_CIPHER = PycaFernet(argv[2])
    ip = argv[0]
    port = int(argv[1])
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.connect((ip, port))
    #sock.setblocking(0)

    plog("main_shark: sending hello msg: \"i_am_shark\"")
    hello_msg = utf8_to_bytes("i_am_shark")
    send_msg(sock, hello_msg)

    pout("What do you want? \n\tPress Enter to get screen from photo \nor \n\tType message and press Enter to send this message to show. ")
    gi = 0
    while(True):
        print("> ", end = "")
        user_input = input()
        if(user_input == ""):
            send_msg(sock, utf8_to_bytes("take_photo") )

            #select.select([sock], [], [])
            bs = recv_msg(sock)
            bs = deform_screen_bytes(bs)
            screen_file_name = f"screen{gi}.png"
            write2file_bytes(screen_file_name, bs)
            gi += 1
            pout(f"Saved screenshot to \"{screen_file_name}\"\n")
        else:
            send_msg(sock, utf8_to_bytes(f"show:{user_input}") )

            #select.select([sock], [], [])
            bs = recv_msg(sock)
            msg = bytes_to_utf8(bs)

            pout(f"Server said: \"{msg}\"")


# ip port
# 0   1
def main_show(argv: list):
    if(len(argv) != 2):
        perr("Sytax error! Expected: \"> python photoshark.py show {ip} {port}\". ")
        exit()
    try:
        global IF_DEBUG_MSG
        IF_DEBUG_MSG = False
        plog("show starting")
        pout("show started. Waiting messages from shark...")
        ip = argv[0]
        port = int(argv[1])
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.connect((ip, port))
        #sock.setblocking(0)

        plog("main_show: sending hello msg: \"i_am_show\"")
        hello_msg = utf8_to_bytes("i_am_show")
        send_msg(sock, hello_msg)
        shit_count = 0
        while(True):
            #select.select([sock], [], [])
            bs = recv_msg(sock)
            msg = bytes_to_utf8(bs)
            pout(f"\nGetted msg: \"{msg}\"\n")
            if(msg == ""):
                plog(f"({shit_count}) Server down?")
                time.sleep(1)
                shit_count += 1
                if(shit_count > 5):
                    plog("Server downed. Reconnecting...")
                    raise "bullshit happened"
            send_msg(sock, utf8_to_bytes("OK") )
    except Exception as eerrrrr:
        print(eerrrrr)
        plog(f"Some bullshit happened. Restarting... ")
        time.sleep(5)
        main_show(argv)

if __name__ == "__main__":
    argc = len(sys.argv)
    if(argc < 2):
        perr("Syntax error. Expected: \"> python photoshark.py {server, photo, shark, show} ...\"")
        exit()
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
        perr("Syntax error. Expected: \"> python photoshark.py {server, photo, shark, show} ...\"")
        exit()

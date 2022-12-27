# -*- coding: utf-8 -*-

import sys
import os
import io
import datetime
import time

import socket
import select

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


SCREEN_CIPHER = None

class AES256CBC_Cipher(object):
	# https://stackoverflow.com/questions/12524994/encrypt-decrypt-using-pycrypto-aes-256

    def __init__(self, key):
        import base64
        import hashlib
        from Crypto import Random
        from Crypto.Cipher import AES
        self.bs = AES.block_size
        self.key = hashlib.sha256(key.encode()).digest()

    def encrypt(self, raw: bytes) -> bytes:
        import base64
        import hashlib
        from Crypto import Random
        from Crypto.Cipher import AES
        raw = base64.b64encode(raw)
        raw = str(raw, "ascii")
        raw = self._pad(raw)
        iv = Random.new().read(AES.block_size)
        cipher = AES.new(self.key, AES.MODE_CBC, iv)
        return base64.b64encode(iv + cipher.encrypt(raw.encode()))

    def decrypt(self, enc: bytes) -> bytes:
        import base64
        import hashlib
        from Crypto import Random
        from Crypto.Cipher import AES
        enc = base64.b64decode(enc)
        iv = enc[:AES.block_size]
        cipher = AES.new(self.key, AES.MODE_CBC, iv)
        return self._unpad(cipher.decrypt(enc[AES.block_size:]))

    def _pad(self, s):
        return s + (self.bs - len(s) % self.bs) * chr(self.bs - len(s) % self.bs)

    @staticmethod
    def _unpad(s):
        return s[:-ord(s[len(s)-1:])]

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
        import base64
        res = SCREEN_CIPHER.decrypt(bs)
        res = base64.b64decode(res)
        return res

# port
#  0
def main_server(argv: list):
    if(len(argv) != 1):
        perr("Sytax error! Expected: \"> python photoshark.py server {port}\". ")
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
                    conn.setblocking(0)

                    select.select([conn], [], [], 0)
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
                            select.select([fds["photo"]], [], [])
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
                            select.select([fds["show"]], [], [])
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


# ip port [cipher_key]
# 0   1         2
def main_photo(argv: list):
    import pyautogui
    if(len(argv) < 2 or len(argv) > 3):
        perr("Sytax error! Expected: \"> python photoshark.py photo {ip} {port} [{cipher_key}]\". ")
    if(len(argv) == 3):
        global SCREEN_CIPHER
        SCREEN_CIPHER = AES256CBC_Cipher(argv[2])
    try:
        plog("photo starting")
        ip = argv[0]
        port = int(argv[1])
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.connect((ip, port))
        sock.setblocking(0)
        
        hello_msg = utf8_to_bytes("i_am_photo")
        send_msg(sock, hello_msg)
        shit_count = 0
        while(True):
            select.select([sock], [], [])
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
    if(len(argv) == 3):
        global SCREEN_CIPHER
        SCREEN_CIPHER = AES256CBC_Cipher(argv[2])
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
        print("> ", end = "")
        user_input = input()
        if(user_input == ""):
            send_msg(sock, utf8_to_bytes("take_photo") )

            select.select([sock], [], [])
            bs = recv_msg(sock)
            bs = deform_screen_bytes(bs)
            screen_file_name = f"screen{gi}.png"
            write2file_bytes(screen_file_name, bs)
            gi += 1
            pout(f"Saved screenshot to \"{screen_file_name}\"\n")
        else:
            send_msg(sock, utf8_to_bytes(f"show:{user_input}") )

            select.select([sock], [], [])
            bs = recv_msg(sock)
            msg = bytes_to_utf8(bs)

            pout(f"Server said: \"{msg}\"")


# ip port
# 0   1
def main_show(argv: list):
    if(len(argv) != 2):
        perr("Sytax error! Expected: \"> python photoshark.py show {ip} {port}\". ")
    try:
        plog("show starting")
        ip = argv[0]
        port = int(argv[1])
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.connect((ip, port))
        sock.setblocking(0)

        hello_msg = utf8_to_bytes("i_am_show")
        send_msg(sock, hello_msg)
        shit_count = 0
        while(True):
            select.select([sock], [], [])
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
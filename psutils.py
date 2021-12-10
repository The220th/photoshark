# -*- coding: utf-8 -*-
import io
import base64

def log(s : str) -> None:
    print(s)

def out(s : str) -> None:
    print(s)

def recv(connection) -> str:
    number = connection.recv(25).decode("utf8")
    number_length = int(number)
    #print(f"{number} : {number_length}")
    i = 0
    resbytedata = b''
    while(i < number_length):
        if(i + 1024 < number_length): 
            data = connection.recv(1024)
            i += 1024
        else:
            dif = number_length - i
            data = connection.recv(dif)
            i += dif
        resbytedata += data
    return resbytedata.decode("utf8")


def send(connection, data : str) -> None:
    toSend = data.encode('utf8')
    length = str(len(toSend))
    length = "0"*(25-len(length)) + length
    connection.send(length.encode('utf8'))
    connection.sendall(toSend)

'''
def recv(connection) -> str:
    data_output = ""
    while True:
        #print(1234)
        data = connection.recv(1024).decode("utf8")
        if(data == "STOP"):
            break
        data_output += data
        if(data_output[-4:] == "STOP"):
            data_output = data_output[:-4]
            break
        #print(f"123: {len(data)}: cur: {data_output}") # piz #dec
    #print(321)
    return data_output

def send(connection, data : str) -> None:
    toSend = data.encode('utf8')
    connection.sendall(toSend)
    connection.send("STOP".encode('utf8')) # python too hard=/
'''

def writeFile(fileName : str, s : str) -> None:
    with open(fileName, 'w', encoding="utf-8") as temp:
        temp.write(s)

def writeFileBytes(fileName : str, b : bytes) -> None:
    with open(fileName, 'wb') as temp:
        temp.write(b)

def image2bytes(image) -> bytes:
    img = image

    img_byte_arr = io.BytesIO()
    img.save(img_byte_arr, format='PNG')
    img_byte_arr = img_byte_arr.getvalue()
    return img_byte_arr


def bytes2str(ba : bytes) -> str:
    ress = io.StringIO()
    for i in range(len(ba)):
        if(i == 0):
            ress.write(str(ba[i]))
        else:
            ress.write("_" + str(ba[i]))
    res = ress.getvalue()
    return res

def str2bytes(s : str) -> bytes:
    #buff = s.split("_")
    a = []
    #for i in buff:
    #    a.append(int(i))
    i = 0
    while(i < len(s)):
        buff = ""
        while(i < len(s) and s[i] != "_"):
            buff += s[i]
            i+=1
        a.append(int(buff))
        i+=1
    ba = bytes(a)
    return ba

'''
def str2bytes(s : str) -> bytes:
    #base64.b64encode(s.encode("utf-8"))
    a = []
    for i in s:
        a.append(ord(i))
    baa = bytes(a)
    ba = base64.b64encode(baa)
    return ba

def bytes2str(ba : bytes) -> str:
    #base64.b64decode(ba).decode("utf-8")
    baa = base64.b64decode(ba)
    ress = io.StringIO()
    for i in baa:
        ress.write(chr(i))
        print(i)
    res = ress.getvalue()
    return res
'''
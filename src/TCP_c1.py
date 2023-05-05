#! /usr/bin/env python3
# _*_ coding: utf-8 _*_

from socket import *
import threading
# from time import (ctime,time)
import time
import json
import traceback
import re
import pyaudio
import os
from progressbar import process_bar
# import sys

# IP = '127.0.0.1' # 
IP = '8.130.21.238' # 使用云服务器时用这个  #
PORT = 8080
PORTUDP = 8060
BUFLEN = 1024
BUFPRELEN = 18 # 前驱报头长度——指示报文类型

# 语音聊天数据
CHUNK = 4096 # 字节
FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 44100
RECORD_SECONDS = 10

local_nickname = "client"
local_username = ""
logFlag = True # True表示未登录
connectFlag = True # True表示未连接聊天
chattingObjectName = "" # 当前正在聊天的对象的username
Document_integrity = 1 # 当文件大小匹配或文件不存在时为1，不完整时为0，对方不在线时为-1
not_receivedQueryForFile = True # 用于忙等
received_size = 0 # 已经接收的文件大小


# 新用户注册(账号username唯一, 需要查重)
def verify_register(sock, usern, pd, nickn):
    username = usern # self.input_account.get()
    password = pd # self.input_password.get()
    nickname = nickn # self.input_nickname.get()
    try:
        register_data = {}
        register_data["type"] = "register"
        register_data["username"] = username
        register_data["password"] = password
        register_data["nickname"] = nickname
        # 将dict类型转为json字符串，便于网络传输
        data = json.dumps(register_data)

        preDataSend = {
            "type": "signup"
        }
        preData = json.dumps(preDataSend)
        sock.send(preData.encode("utf-8"))
        sock.send(data.encode("utf-8"))
        # print("register_data: ", register_data)
    except:
        traceback.print_exc()

# 用户登录(验证登录账号和密码)
def verify_login(sock, usern, pd):
    account = usern # self.input_account.get()
    password = pd # self.input_password.get()
    try:
        login_data = {}
        login_data["type"] = "login"
        login_data["username"] = account
        login_data["password"] = password
        data = json.dumps(login_data)

        preDataSend = {
            "type": "signin"
        }
        preData = json.dumps(preDataSend)

        print(data)

        sock.send(preData.encode("utf-8"))
        sock.send(data.encode('utf-8'))
        # print("login_data: ",login_data)
    except:
        traceback.print_exc()

def recv_File(headInfo_dict, userFrom, type):
    '''
    接收大文件,返回文件名
    headinfo structure:
        head_dir = {
            "type": "file", //or "filecontinuation"
            "filename": 'new' + filename,
            "filesize_bytes": filesize_bytes,
        }
    '''
    filename = headInfo_dict['filename']
    filesize_b = headInfo_dict['filesize_bytes']
    recv_len = 0
    recv_mesg = b''

    if type == "file":
        # 正常的完整文件数据
        # width = 50
        f = open(filename, 'wb')
        start_time = time.time()
        while recv_len < filesize_b:
            percent = recv_len / filesize_b
            process_bar(percent) # 进度条
            # print('\rReceiving[%s%s]%d%%' % ((int(percent * width))*'#', (int(width - int(percent * width)))*' ', percent * 100), flush = True, end = '\r')

            if filesize_b - recv_len > BUFLEN:
                recv_mesg = userFrom.recv(BUFLEN)
                recv_len += len(recv_mesg)
                f.write(recv_mesg)
            else:
                recv_mesg = userFrom.recv(filesize_b - recv_len)
                recv_len += len(recv_mesg)
                f.write(recv_mesg)
        # 100%
        percent = recv_len / filesize_b
        process_bar(percent) # 进度条
        # print('\rReceiving[%s%s]%d%%' % ((int(percent * width))*'#', (int(width - int(percent * width)))*' ', percent * 100), flush = True, end = '\r')

        final_time = time.time()
        f.close()
        timeStamp = float(final_time - start_time)
        readable_len = float(recv_len)/1024/1024
        print('\n文件大小:%sB(%.2fMB), 总用时:%.1fs, %s 传输完成.' % (recv_len, readable_len, timeStamp, filename))
        
    elif type == "filecontinuation":
        # 断点续传的数据

        # 寻找本地同名文件，并且计算大小，打印断点进度，开始计时
        flag, has_size = searchFilenameFilesize(filename)
        percent = has_size / (filesize_b + has_size)
        process_bar(percent) # 进度条
        time.sleep(1)   # 让断点续传的痕迹明显一点

        start_time = time.time()

        # 打开文件，读写指针移动
        with open(filename, 'ab') as f: # 追加模式！！！
            while recv_len < filesize_b:
                percent = (recv_len + has_size) / (filesize_b + has_size)
                process_bar(percent) # 进度条

                if filesize_b - recv_len > BUFLEN:
                    recv_mesg = userFrom.recv(BUFLEN)
                    recv_len += len(recv_mesg)
                    f.write(recv_mesg)
                else:
                    recv_mesg = userFrom.recv(filesize_b - recv_len)
                    recv_len += len(recv_mesg)
                    f.write(recv_mesg)
            percent = (recv_len + has_size) / (filesize_b + has_size)
            process_bar(percent) # 进度条
        # 循环接收数据，打印进度（断点进度继续）
        final_time = time.time()
        f.close()
        timeStamp = float(final_time - start_time)
        readable_len = float(recv_len)/1024/1024
        print('\n续传的大小:%sB(%.2fMB), 用时:%.1fs, 文件总大小:%sB(%.2fMB), %s 传输完成.' 
                        % (recv_len, readable_len, timeStamp, recv_len+has_size, float((recv_len+has_size)/1024/1024),filename))
    else:
        pass

    



def searchFilenameFilesize(filename):
    '''
    寻找是否有同名文件，返回是否与文件大小
    '''
    path = os.getcwd()
    for catalog in os.listdir(path):
        newDir = os.path.join(path, catalog)
        if os.path.isfile(newDir) and catalog == filename:
            s = os.path.getsize(filename)
            if s != 0:
                return True, s
    return False, 0




# 接收数据
def recvFrom(data_socket):
    global local_nickname
    global logFlag
    global connectFlag
    global Document_integrity, not_receivedQueryForFile, received_size
    while True and not(logFlag): # 只有登录之后才能从这里收到消息，否则必须从chat函数处理登录注册消息
        try:
            dataPre = data_socket.recv(BUFPRELEN).decode("utf-8") # 这里后面需要判断报文类型##########
            dataPre_dict = json.loads(dataPre)
            
            if dataPre_dict["type"] == "fileee": # 如果接收的是文件，转文件传输处理
                headLength = data_socket.recv(30)
                headLength_dict = json.loads(headLength.decode('utf-8')) # 解码并反序列化
                headinfoLength = headLength_dict["length"]              # 解析得到报头信息的长度

                headInfo = data_socket.recv(headinfoLength)
                headInfo_dict = json.loads(headInfo.decode('utf-8')) 
                print("\r----------------", headInfo_dict["type"])
                recv_File(headInfo_dict, data_socket, headInfo_dict["type"])     # filecontinuation file
                # print('\n%s: ' % local_nickname, end='')
                if connectFlag == True: print("\ncommand>>> ", flush = True, end = '')
                else: print('\n%s: ' % local_nickname, flush = True, end = '')            

            elif dataPre_dict["type"] == "queryf": # 如果接收的是探寻信息，搜索本地文件系统之后，给出答复，send的对象是
                
                Integrity = False # 目标文件不存在
                data = data_socket.recv(BUFLEN).decode("utf-8")
                data_dict = json.loads(data)
                object_filename = "newnew" + data_dict["filename"]
                origin_size = data_dict["size"]

                # 遍历当前文件目录下所有文件名
                Integrity, size = searchFilenameFilesize(object_filename)

                preDataSend = {
                    "type": "respof"
                }
                preData = json.dumps(preDataSend)
                if Integrity:
                    response = {}
                    response["type"] = "respof"
                    response["has_size"] = size
                    response["origin_size"] = origin_size
                    response["Initiator_username"] = data_dict["username"]

                    print("has_size, origin_size, Initiator_username: ", size, origin_size, data_dict["username"])

                    respo_data = json.dumps(response)
                    data_socket.send(preData.encode("utf-8")) # 发送预处理报文-18字节
                    data_socket.send(respo_data.encode("utf-8")) # 发送response
                else:
                    response = {}
                    response["type"] = "respof"
                    response["has_size"] = 0
                    response["origin_size"] = origin_size
                    response["Initiator_username"] = data_dict["username"]

                    print("has_size, origin_size, Initiator_username: ", 0, origin_size, data_dict["username"])


                    respo_data = json.dumps(response)
                    data_socket.send(preData.encode("utf-8")) # 发送预处理报文-18字节
                    data_socket.send(respo_data.encode("utf-8")) # 发送response
                print("\n已发送response信息,Integrity:%s\n" % Integrity)


            elif dataPre_dict["type"] == "respof":
                print("respof-------------get")
                data = data_socket.recv(BUFLEN).decode("utf-8")
                data_dict = json.loads(data)

                if data_dict["has_size"] == -1:
                    print("对方暂时不在线.即将传输离线文件...")
                    Document_integrity = -1
                    not_receivedQueryForFile = False
                elif data_dict["has_size"] == 0 or data_dict["origin_size"] - data_dict["has_size"] == 0: # data_dict["has_size"] == data_dict["origin_size"]:
                    Document_integrity = 1   # 文件不存在，直接传输即可
                    not_receivedQueryForFile = False
                else:
                    received_size =  data_dict["has_size"]
                    Document_integrity = 0  # 文件需要断点续传
                    not_receivedQueryForFile = False


            elif dataPre_dict["type"] == "update":              # 返回用户在线的消息
                data = data_socket.recv(BUFLEN).decode("utf-8")
                data_dict = json.loads(data)
                print("\r用户在线情况:")
                msg = data_dict["update_user"]
                for i in range(len(msg)):   print('\t', msg[i][0].ljust(10), msg[i][1].ljust(10))
                print("")
                # print('\n%s>>> ' % local_nickname, end = '')
                print("command>>> ", flush = True, end = '')

            elif dataPre_dict["type"] == "connec":              # 主动连接用户私聊
                data = data_socket.recv(BUFLEN).decode("utf-8")
                data_dict = json.loads(data)
                # print(data_dict)
                msg = data_dict["message"].strip()
                if "000" == data_dict["code"]:
                    connectFlag = False
                    print("\rConnect OK.", msg)
                    print('\n%s: ' % local_nickname, flush = True, end = '')
                    # print("command>>> ", end = '')
                else:
                    print("\rConnect request dennied. [Cause]%s" % msg)
                    print("")
                    print("command>>> ", flush = True, end = '')

            elif dataPre_dict["type"] == "groupp":              # 群聊
                data = data_socket.recv(BUFLEN).decode("utf-8")
                data_dict = json.loads(data)
                msg = data_dict["message"].strip()
                if "000" == data_dict["code"]:
                    connectFlag = False
                    print("\rGroupchat ready. GroupName: [%s]\n%s" % (data_dict["groupname"], msg))
                    print('\n%s: ' % local_nickname, flush = True, end = '')
                else:
                    print("\rRequest dennied. [Cause]%s" % msg)
                    print("")
                    print("command>>> ", flush = True, end = '')
                

            elif dataPre_dict["type"] == "logout":
                # print("\rLog out successfully.")
                continue
                
            else:                                # 其他情况：文字聊天数据包
                data = data_socket.recv(BUFLEN).decode("utf-8")
                data_dict = json.loads(data)
                message = data_dict["message"].strip()
                nickname = data_dict["nickname"].strip()
                if message == 'END':
                    print("\rPRESENT CHAT ENDED.")
                    # print('\n%s>>> ' % local_nickname, end = '')
                    if connectFlag == True: print("command>>> ", flush = True, end = '')
                    else: print('%s: ' % local_nickname, flush = True, end = '')
                    # data_socket.close()
                    # return True
                    # break
                else:
                    # print("nickname", nickname)
                    if connectFlag == True: 
                        if dataPre_dict["type"] == "signin":
                            print('\r[%s]\n%s' % (time.ctime(), nickname), ':\n\t%s' % message, '\n\ncommand>>> ', end='')
                        else:
                            print('\r[%s]\n%s' % (time.ctime(), nickname), ':', message, '\n\ncommand>>> ', end='')
                    else: print('\r[%s]\n%s' % (time.ctime(), nickname), ':', message, '\n\n%s: ' % local_nickname, end='')
                    # if connectFlag == True and logFlag == False: print('\r[%s]\n%s' % (ctime(), nickname), ':', message, '\n\ncommand>>> ', end='')
                    # elif connectFlag == False and logFlag == False: print('\r[%s]\n%s' % (ctime(), nickname), ':', message, '\n\n%s: ' % local_nickname, end='')
                    # else: pass
        # except (ConnectionAbortedError, ConnectionResetError):
        #     print("客户端与服务器端断开连接")
        #     data_socket.close()
        #     return
        except:
            print("\rPRESENT CHAT ENDED DUE TO OSError-1.")
            # traceback.print_exc()
            data_socket.close()
            return  # find it was close, then close it
        

# 模式选择(登录、注册、退出)
def initialize(data_socket):
    unvalidinput = True
    while unvalidinput:
        print('{0:^11}'.format('\t\t\t-------------------Client初始界面-------------------') + "\n选项: 1-登录 2-注册 3-退出")
        mode = input("输入: ")
        if mode == '3':
            print("User exit.")
            return -1
        elif mode == '2':
            try:
                usern, pd, nickn = input('输入username password nickname(空格隔开):').split()
                verify_register(data_socket, usern, pd, nickn)
                unvalidinput = False
                return 0
            except:
                print("抱歉, 格式错误, 请检查输入格式.", flush = True)
                pass

        elif mode == '1':
            try:
                usern, pd = input('输入username password(空格隔开):').split()
                verify_login(data_socket, usern, pd)
                unvalidinput = False
                return 0
            except:
                print("抱歉, 格式错误, 请检查输入格式.", flush = True)
                pass
        else:
            print("Error occurred.")
            return -1


def pretreatFile(filename, filepath):
    '''
    对报头进行打包, 发送文件大小的预处理报文
    '''
    filesize_bytes = os.path.getsize(filepath) # 字节为单位
    head_dir = {
        "type": "file",
        "filename": 'new' + filename,
        "filesize_bytes": filesize_bytes,
    }
    
    # json.dumps() 是把python对象转换成json对象的一个过程，生成的是字符串
    head_info = json.dumps(head_dir) # 报头信息
    prehead = {
        "type": "file",
        "length": len(head_info)
    }
    # struct.pack 按照给定的格式(fmt)——这里为i——int,把数据转换成字符串(字节流),并将该字符串返回. # head_info_len = struct.pack('i', len(head_info)) # 报头的长度信息
    head_info_len = json.dumps(prehead)  # head_info_len长度为30，即len(head_info_len)==30
    return head_info_len, head_info


def sendFiletoServer(sock, filename):
    '''
    发送文件内容
    '''
    with open(filename, 'rb') as f:
        sock.sendall(f.read())
    print('%s 发送成功' % filename)


def sendFiletoServer_continuation(data_socket, filepath, received_size, size):
    '''
    发送断点续传的文件内容
    ''' 
    with open(filepath, 'rb') as f:
        f.seek(received_size)  # 定位到已经传到的位置
        data_socket.sendall(f.read())
        # while received_size < size:
        #     data = f.read(1024)
        #     data_socket.sendall(data)
        #     received_size += len(data)
        #     # time.sleep(0.2)
        #     print('\r已发送%s%%|%s' % (int(received_size/size*100), (round(received_size/size*40)*'★')), flush = True, end = '')
    print("断点续传完毕\n")





def queryOnlineUsers(data_socket):
    try:
        update_data = {}
        update_data["type"] = "update"
        data = json.dumps(update_data)

        preDataSend = {
            "type": "update"
        }
        preData = json.dumps(preDataSend)
        data_socket.send(preData.encode("utf-8"))
        data_socket.send(data.encode('utf-8'))
    except:
        traceback.print_exc()

def chatwithUser(username, data_socket):
    try:
        connect_data = {}
        connect_data["type"] = "connec"
        connect_data["connect_username"] = username
        data = json.dumps(connect_data)

        preDataSend = {
            "type": "connec"
        }
        preData = json.dumps(preDataSend)
        data_socket.send(preData.encode("utf-8"))
        data_socket.send(data.encode('utf-8'))
    except:
        traceback.print_exc()

def chatinGroup(groupname, username, data_socket):
    try:
        group_data = {}
        group_data["type"] = "groupp"
        group_data["username"] = username
        group_data["groupname"] = groupname
        data = json.dumps(group_data)

        preDataSend = {
            "type": "groupp"
        }
        preData = json.dumps(preDataSend)
        data_socket.send(preData.encode("utf-8"))
        data_socket.send(data.encode('utf-8'))
    except:
        traceback.print_exc()


# 语音聊天
def callback(in_data, frame_count, time_info, status):
        # in_data:      如果input=True，in_data就是录制的数据，否则为None
        # frame_count:  帧的数量，表示本次回调要读取几帧的数据
        # time_info:    一个包含时间信息的dict，略
        # status:       状态标志位，略
    # print("len: ",len(in_data))
    soc.sendto(in_data, myPeer)
    # print("* done sending")
    return (in_data, pyaudio.paContinue)

# 语音通话
def audioCalltoSingleUser(usernameTo, username, data_socket):
    global soc, myPeer, signature, peerConnected, STOPflag
    peerConnected = False
    STOPflag = True
    soc = socket(AF_INET, SOCK_DGRAM)
    # serverAddress = ('127.0.0.1', 8080)
    serverAddress = (IP, PORTUDP)
    try:
        group_data = {}
        group_data["type"] = "voicee"
        group_data["username"] = username
        group_data["userTo"] = usernameTo
        data = json.dumps(group_data)

        preDataSend = {
            "type": "voicee"
        }
        preData = json.dumps(preDataSend)
        data_socket.send(preData.encode("utf-8"))
        data_socket.send(data.encode('utf-8'))
    except:
        traceback.print_exc()

    # 连接服务器
    chain = input('连接口令：')
    send = (chain).encode()
    soc.sendto(send, serverAddress)
    message = eval(soc.recvfrom(2048)[0].decode())
    myPeer = tuple(message[0])
    signature = str(message[1])
    print('got myPeer: ', myPeer)

    peerConnected = False
    sen_thread = threading.Thread(target = sendToMyPeer)
    rec_thread = threading.Thread(target = recFromMyPeer)
    rec_thread.setDaemon(True)
    sendstop =  threading.Thread(target = ttt)

    sen_thread.start()
    rec_thread.start()
    sendstop.start()

    sen_thread.join()
    # print("Call End-1.")
    # rec_thread.join()
    # print("Call End-0.")
    sendstop.join()
    # print("Call End.")

#先连接myPeer，再互发消息
def sendToMyPeer():
    #发送包含签名的连接请求
    global peerConnected, STOPflag
    while True:
        soc.sendto(signature.encode(), myPeer)
        if peerConnected:
            break
        time.sleep(1)
    
    #发送聊天信息
    p = pyaudio.PyAudio()
    stream = p.open(format=FORMAT,
                        channels=CHANNELS,
                        rate=RATE,
                        input=True,
                        stream_callback=callback,
                        frames_per_buffer=CHUNK)
    stream.start_stream()
    
    while STOPflag:
        time.sleep(0.5) #休眠，不影响录音
    # time.sleep(RECORD_SECONDS)

    stream.stop_stream()
    print("* done recording")
    stream.close()
    p.terminate()


def recFromMyPeer():
    #接收请求并验证签名or接收聊天信息
    global peerConnected, STOPflag
    F = True
    p = pyaudio.PyAudio()
    streamRec = p.open(format=FORMAT,
                        channels=CHANNELS,
                        rate=RATE,
                        output=True,
                        frames_per_buffer=CHUNK)
    while STOPflag:
        try:
            if F:
                message = soc.recvfrom(4096)[0].decode()
            else:
                message = soc.recv(8192)  # ?why? 为什么不是4096
            if message == signature:
                if not peerConnected:
                    print('connected successfully')
                peerConnected = True
                F = False
            elif peerConnected:
                streamRec.write(message)       # stream.write(frame, CHUNK)
        except:
            # print("damn it")
            traceback.print_exc()
        
    streamRec.stop_stream()
    # print("* done receiving")
    streamRec.close()
    p.terminate()

def ttt():
    global STOPflag
    while STOPflag:
        a = input("Press only 'ENTER' to end...")
        if a == "":
            STOPflag = False
            # print("Stopflag:", STOPflag)
            break
        else:
            continue
            # print("Stopflag:", STOPflag)
    # print("ttt End.")





# def chooseChatting(data_socket):
#     '''
#     选择一个（在线？）用户私聊
#     '''
#     pattern = re.compile('(chatwith)\s(.*)', re.S)
#     while True:
#         # print('%s>>> ' % local_nickname, end = '')
#         lineinput = input("command>>> ")
#         if (lineinput == "update"):
#             queryOnlineUsers(data_socket)

#             dataPre = data_socket.recv(BUFPRELEN).decode("utf-8")
#             data = data_socket.recv(BUFLEN).decode("utf-8")
#             data_dict = json.loads(data) # 根据服务器端返回的type值，执行不同逻辑
#             print("用户在线情况：")
#             msg = data_dict["update_user"]
#             for i in range(len(msg)):
#                 print('\t', msg[i][0], '--\t',msg[i][1])

#         elif (pattern.findall(lineinput)):
#             '''
#             chatwith Emma
#             '''
#             chatwithUser(pattern.findall(lineinput)[0][1], data_socket)

#             dataPre = data_socket.recv(BUFPRELEN).decode("utf-8")
#             data = data_socket.recv(BUFLEN).decode("utf-8")
#             data_dict = json.loads(data) # 根据服务器端返回的type值，执行不同逻辑

#             print(data_dict)
#             msg = data_dict["message"].strip()
#             if "000" == data_dict["code"]:
#                 print("connect OK.", msg)
#                 return False # 用户间连接成功，退出连接环节
#             else:
#                 print("Connect request dennied.[Cause]", data_dict["msg"])
#         else:
#             continue

        # elif (lineinput == "logout"):##############################
        # elif (lineinput == "logout"):##############################


# 聊天
def chatting(data_socket):
    global local_nickname, local_username
    global logFlag, connectFlag
    global chattingObjectName
    global Document_integrity, not_receivedQueryForFile, received_size
    # 初始化和身份认证\以及update和connect私聊发起
    while True:
        print("提示logFlag: ", logFlag)
        while (logFlag): 
            # 没有登录时进入此循环
            if(logFlag == True): # 登录or注册
                if(initialize(data_socket) == -1): return True
            try:
                dataPre = data_socket.recv(BUFPRELEN).decode("utf-8")
                data = data_socket.recv(BUFLEN).decode("utf-8")
                data_dict = json.loads(data) # 根据服务器端返回的type值，执行不同逻辑
                # print(data_dict)
                type = data_dict["type"]
                msg = data_dict["msg"].strip()
                # 登录
                if type == "login":
                    # 登录成功，跳转聊天
                    if "000" == data_dict["code"]:
                        print("Login OK.", msg)
                        print("")
                        local_nickname = data_dict["nickname"]
                        local_username = data_dict["username"]
                        logFlag = False
                        break # 登录成功，退出认证环节
                    else:
                        print("Login request dennied. [Cause]%s" % data_dict["msg"])
                # 注册
                elif type == "register":
                    if "000" == data_dict["code"]:
                        print("Registration OK.", msg) # 注册成功
                        print("")
                        local_nickname = data_dict["nickname"]      
                        logFlag = False              
                        break # 注册并登录成功，退出认证环节
                    else:
                        print("Registration request dennied. [Cause]%s" % data_dict["msg"])
                else:
                    print("Unexpected flag.")

                # if Beconnected == False:
                #     if (logFlag == False and connectFlag == True): # 已经登录还未连接聊天
                #         connectFlag = chooseChatting(data_socket)
                #         print("connectFlag:",connectFlag)
                # else:
                #     print("Has been connected by other users.")
                #     connectFlag = False
                
                # print("logFlag connectFlag:",logFlag, connectFlag)
            except OSError:
                print("\rPRESENT CHAT ENDED DUE TO OSError-2.")


        # 接收数据
        threadrev = threading.Thread(target = recvFrom, args=(data_socket, ))
        # print("1线程：", threadrev.is_alive())
        # if threadrev.is_alive(): threadrev.join() 
        threadrev.setDaemon(True) 
        # 发送和接收是两个独立的过程，原本主线程结束，子线程会自己继续执行
        # 设置为守护线程会导致主线程结束之后，子线程被迫终止，加上join之后主线程会在join处等待子线程
        # threadrev.join()就是为了防止停止发送之后，无法接收数据导致异常，但是现在发现断开连接就应该完全断开...所以不能加这个join
        threadrev.start()
        # print("2线程：", threadrev.is_alive())

        pattern = re.compile('(filetrans)\s([a-zA-Z]:\/(?:.*?\/)*(.*))', re.S) # if re正则匹配的结果是一个发送文件的操作 filetrans
        pattern2 = re.compile('(chatwith)\s(.*)', re.S)
        pattern3 = re.compile('(groupchat)\s(.*)', re.S)
        pattern4 = re.compile('(call)\s(.*)', re.S)
        # 主线程继续发送数据，新线程用于接收数据
        while True:
            # time.sleep(0.5)

            if connectFlag == True: print("command>>> ", end = '')
            else: print('%s: ' % local_nickname, end = '')
            toSend = input() 
            # print('\r[%s]\n%s' % (ctime(), local_nickname), ':', toSend)
            print('')
            
            if (toSend == "update" and connectFlag == True):
                '''
                更新在线用户数据
                '''
                queryOnlineUsers(data_socket)

            elif (toSend == "help"):
                '''help'''
                print("Valid input:")
                print("\tupdate\t\t\t-\t更新用户的在线数据\n\tchatwith (username)\t-\t和用户名为username的用户聊天\n\tcall (username)\t\t-\t和名为username的用户语音聊天\n\tgroupchat (groupname)\t-\t加入名为groupname的群聊\n\tfiletrans (filePath)\t-\t将文件绝对路径为filePath的文件发送给对方\n\tEND\t\t\t-\t结束当前聊天\n\tLOGOUT\t\t\t-\t退出当前账号")

            elif (pattern2.findall(toSend)):
                '''
                用户间1v1线程
                test: chatwith Emma
                '''
                if(pattern2.findall(toSend)[0][0] == "chatwith" and pattern2.findall(toSend)[0][1] != None):
                    print("User to chat with:", pattern2.findall(toSend)[0][1])
                    chatwithUser(pattern2.findall(toSend)[0][1], data_socket)
                    chattingObjectName = pattern2.findall(toSend)[0][1]

            elif (pattern3.findall(toSend)):
                '''
                groupchat
                '''
                if(pattern3.findall(toSend)[0][0] == "groupchat" and pattern3.findall(toSend)[0][1] != None):
                    groupname = pattern3.findall(toSend)[0][1]
                    print("Join in the group [%s]" % groupname)
                    chatinGroup(groupname, local_username, data_socket)
            

            elif (pattern4.findall(toSend)):
                '''
                voicecall
                '''
                if(pattern4.findall(toSend)[0][0] == "call" and pattern4.findall(toSend)[0][1] != None):
                    usernameTo = pattern4.findall(toSend)[0][1]
                    print("Voice call to [%s]" % usernameTo)
                    audioCalltoSingleUser(usernameTo, local_username, data_socket)
                    print("Audio channel closed.\n")
            
            elif (pattern.findall(toSend)): 
                '''
                发送文件 命令格式: filetrans(空格)文件绝对路径 (注意路径中分级符号使用/而不是\)
                test: filetrans C:/Users/123/vscode-pythonworkspace/XJTUcourse/Network/socket/version1/video.mp4  44M
                test: filetrans C:/Users/123/vscode-pythonworkspace/XJTUcourse/Network/socket/version1/book.pdf  122M
                test: filetrans C:/Users/123/vscode-pythonworkspace/XJTUcourse/Network/socket/version1/latex.pdf   1.38M
                '''
                keyWordtoSend = pattern.findall(toSend)[0][0]
                if (keyWordtoSend == "filetrans"):
                    filepath = pattern.findall(toSend)[0][1]
                    filename = pattern.findall(toSend)[0][2]
                    not_receivedQueryForFile = True

                    # print(not_receivedQueryForFile, Document_integrity)

                    # switch = input("是否使用包括断点续传的文件传输?[Y/N]")
                    ### 探寻报文，询问对方用户文件是否存在，文件是否完整 ###
                    preDataSend = {
                        "type": "queryf"
                    }
                    preData = json.dumps(preDataSend)
                    data_socket.send(preData.encode("utf-8")) # 发送预处理报文-18字节
                    size = os.path.getsize(filepath)

                    # 查询文件发送的目的方是否有目标文件
                    query_data = {}
                    query_data["type"] = "queryf"
                    query_data["username"] = local_username
                    query_data["targetname"] = chattingObjectName
                    query_data["filename"] = filename
                    query_data["size"] = size

                    data = json.dumps(query_data)
                    data_socket.send(data.encode('utf-8'))
                   
                    while not_receivedQueryForFile: # 忙等, 查询文件发送目的方是否已经有目标文件了
                        time.sleep(1)

                    print("是否传输完整文件:", Document_integrity)

                    if Document_integrity == 1 or Document_integrity == -1:  # 直接传输完整文件即可
                        print("About to send file [%s]. Sending file ..." % filename)
                        preDataSend = {
                            "type": "fileee"
                        }
                        preData = json.dumps(preDataSend)
                        data_socket.send(preData.encode("utf-8")) # 发送预处理报文-18字节
                        
                        head_info_len, head_info = pretreatFile(filename, filepath) 
                        
                        #重新设计head——info——len的报文结构，服务器只需要转发即可
                        data_socket.send(head_info_len.encode('utf-8'))  # 这里是30个字节(发送报头长度)
                        data_socket.send(head_info.encode('utf-8'))  # 发送报头的内容(包括报文类型file、文件名和文件大小)
                        # 发送文件内容
                        sendFiletoServer(data_socket, filepath) # socket和文件名(包括扩展名)
                        print('')
                    else:
                        print("对方文件不完整，断点续传准备中......")
                        print("对方已接收的文件大小: %.2fMB" % float(received_size/1024/1024))
                        left_size = size - received_size # 待接收的文件大小

                        # 断点续传需要接收端进行接收文件的定位工作！！！！！！！##############
                        preDataSend = {
                            "type": "fileee"  # 1
                        }
                        preData = json.dumps(preDataSend)
                        data_socket.send(preData.encode("utf-8")) # 发送预处理报文-18字节
                        
                        '''
                        对报头进行打包, 发送文件大小的预处理报文
                        '''
                        # filesize_bytes = os.path.getsize(filepath) # 字节为单位
                        head_dir = {
                            "type": "filecontinuation",  # 意为断点续传报文 # 3
                            "filename": 'new' + filename,
                            "filesize_bytes": left_size
                        }
                        
                        # json.dumps() 是把python对象转换成json对象的一个过程，生成的是字符串
                        head_info = json.dumps(head_dir) # 报头信息
                        prehead = {
                            "type": "file",         # 2
                            "length": len(head_info)
                        }
                        # struct.pack 按照给定的格式(fmt)——这里为i——int,把数据转换成字符串(字节流),并将该字符串返回. # head_info_len = struct.pack('i', len(head_info)) # 报头的长度信息
                        head_info_len = json.dumps(prehead)  # head_info_len长度为30，即len(head_info_len)==30

                        #重新设计head——info——len的报文结构，服务器只需要转发即可
                        data_socket.send(head_info_len.encode('utf-8'))  # 这里是30个字节(发送报头长度)
                        data_socket.send(head_info.encode('utf-8'))  # 发送报头的内容(包括报文类型file、文件名和文件大小)
                        # 发送文件内容
                        sendFiletoServer_continuation(data_socket, filepath, received_size, size) # socket和文件名(包括扩展名)
                        # print('')
                        
            elif (toSend == "LOGOUT" and connectFlag == True):
                '''
                退出登录
                '''
                logFlag = True
                account_data = {}
                account_data["type"] = "logout"
                account_data["username"] = local_username
                data = json.dumps(account_data)
                preDataSend = {
                    "type": "logout"
                }
                preData = json.dumps(preDataSend)
                data_socket.send(preData.encode("utf-8"))
                data_socket.send(data.encode('utf-8'))
                break

            else:
                '''
                文字聊天
                '''
                chat_data = {}
                chat_data["type"] = "chat"
                chat_data["message"] = toSend
                chat_data["username"] = local_username
                chat_data["nickname"] = local_nickname
                data = json.dumps(chat_data)
                preDataSend = {
                    "type": "chattt"
                }
                preData = json.dumps(preDataSend)
                data_socket.send(preData.encode("utf-8"))
                data_socket.send(data.encode('utf-8'))
  
                if toSend == 'END':
                    chattingObjectName = ''
                    connectFlag = True # 取消输入屏蔽限制，可以识别update\chatwith关键字
                    continue
                # elif toSend == 'LOGOUT':
                #     logFlag = True
                #     break
        # threadrev.join() # 主线程阻塞，直到所有子线程结束之后才结束

if __name__ == '__main__':
    # 实例化了一个socket对象，赋给变量data_socket
    data_socket = socket(AF_INET, SOCK_STREAM)

    # 调用connect方法，连接服务器，connet就是连接正在等待的服务器端的listen_socket
    try:
        data_socket.connect((IP, PORT))
        print("从%s成功连接到%s" % (data_socket.getsockname(), data_socket.getpeername()))

        chatting(data_socket) # 接收消息和发送消息
    except:
        print("Done.")
        data_socket.close() # 用于主动关闭连接的进程关闭套接字

#! /usr/bin/env python3
# _*_ coding: utf-8 _*_

# from socket import *
import socket
import threading
import json
import time
import traceback
import serverReply

# 变量名大写，约定作为配置项的意思，这里定义了三个配置变量作为实例化的参数
# 定义IP地址、端口、缓存，缓存的单位是Byte 
# IP = '127.0.0.1' # 
IP = ''  # 使用云服务器时用这个 #
PORT = 8080
PORTUDP = 8060
BUFLEN = 1024
BUFPRELEN = 18
BUFPREFILELEN = 30
# accessFlag = True # 当前用户是否登录
# chatFlag = True # 当前用户是否已经选择一个用户聊天

ServerUsersPool = [] # 用户列表
'''
ServerSaved_Users = {
    "username": None,
    "nickname": None,
    "onlineFlag":False, # True False
    "socket": None
} # 用户信息结构
'''


# voice call
addressList = []
messageList = []

# 封装线程类以获取返回值
class MyThread(threading.Thread):

    def __init__(self,func,args=()):
        super(MyThread,self).__init__() # 对继承自父类的属性进行初始化。而且是用父类的初始化方法来初始化继承的属性。
        self.func = func
        self.args = args

    def run(self):
        self.result = self.func(*self.args)

    def get_result(self):
        try:
            return self.result  # 如果子线程不使用join方法，此处可能会报没有self.result的错误
        except Exception:
            return None


# 实现用户之间消息接收并转发的功能
def transmitData(sock1, sock2, User2name, chatFlag, groupname, groupFlag, BUFSIZ):
    while True:
        # 从sock1接收数据
        try:
            # 先解析用于报文类型说明的报头
            dataPre = sock1.recv(BUFPRELEN)
            dataPre = dataPre.decode('utf-8')
            dataPre_dict = json.loads(dataPre)
            
            if dataPre_dict["type"] == "fileee": # 如果发送的是文件，转文件传输处理
                serverReply.transmitFile(sock1, sock2, User2name)
            # elif 
            else:                                # 其他情况：对数据包的类型进行判断：聊天数据包\queryf数据包
                data = sock1.recv(BUFSIZ)
                flagSocket = receivedandSend(dataPre, data, sock1, sock2, User2name, groupname, groupFlag)
                if flagSocket == False: 
                    chatFlag = True
                    groupFlag = False
                    return chatFlag, groupFlag # 这步很重要，退出循环
                    # break 

        except (ConnectionAbortedError, ConnectionResetError):
            # 将连接对象从监听列表去掉
            print("客户端与服务器端断开连接-0")
            traceback.print_exc()
            sock1.close()
            sock2.close()
            break
        except Exception:
            # print("OSError occurred")
            print("客户端发生了其它异常-0: ")
            traceback.print_exc()
            sock1.close()
            sock2.close()
            break

# # 给单一客户端发送消息
# def dockingClient(data_socket):
#     # 尝试读取客户端发来的消息
#    # BUFLEN指定从接收缓冲里最多读取多少Bytes，recved是一个字节串变量
#     recved = data_socket.recv(BUFLEN)
# #    # 如果返回空的Bytes，意味着对方关闭了连接
# #    # 退出循环，结束消息收发
# #     if not recved:
# #         break
#    # 把读取的Bytes数据，转换成字符串编码，赋值给变量info，然后打印出来
#     info = recved.decode('utf-8')
#     print(f'Server>>> 收到客户端{ip_port}消息: {info}')

#    # 通知客户端的字符串，编码为utf-8的Bytes类型数据
#     data_socket.send(f'Server>>> 服务器{(IP, PORT)}收到消息 {info}'.encode('utf-8'))
#     data_socket.close()

# 对客户端的请求内容做处理(用于已经登录成功，并且新建了聊天线程的用户之间的通信)
def receivedandSend(dataPre, data, sockUser1, sockUser2, User2name, groupname, groupFlag):
    # 将字节数据解码成字符串
    data = data.decode('utf-8')
    print(data)
    data_dict = json.loads(data)
    dataPre_dict = json.loads(dataPre)

    shutValue = True
    # 聊天
    if dataPre_dict["type"] == "chattt":
        shutValue = serverReply.chat(data_dict, sockUser1, sockUser2, User2name, groupname, groupFlag)
    elif dataPre_dict["type"] == "queryf":
        shutValue = serverReply.queryForFileSituation(data_dict, sockUser1, sockUser2, User2name)
    elif dataPre_dict["type"] == "respof":    
        # print("receivedandSend________testforfile\n")
        shutValue = serverReply.testforfile(data_dict, sockUser2)
    else:
        print("Error!!")
    # # 文件发送
    # elif dataPre_dict["type"] == "fileee":
    #     serverReply.transmitFile(data_dict, sockUser1, sockUser2)
    return shutValue

# 专门处理用户登录、用户注册、在线用户信息查询
def accountProcessing(dataPre, data, data_socket, accessFlag, chatFlag, groupFlag):
    # 将字节数据解码成字符串
    data = data.decode('utf-8')
    print("\n",data)
    data_dict = json.loads(data)
    dataPre_dict = json.loads(dataPre)

    ObjectUser = None
    groupName = ''
    # 根据type字段的值，进入对应的逻辑
    # 登录
    if dataPre_dict["type"] == "signin":
        accessFlag = serverReply.login(data_dict, data_socket)
    # 注册
    elif dataPre_dict["type"] == "signup":
        accessFlag = serverReply.register(data_dict, data_socket)
    # 更新在线和不在线的用户信息
    elif dataPre_dict["type"] == "update":
        serverReply.updateUserOnline(data_dict, data_socket)
    # 用户之间私聊的线程建立
    elif dataPre_dict["type"] == "connec":
        chatFlag, ObjectUser = serverReply.connectToUserOnline(data_dict, data_socket)
    # 群聊建立或加入
    elif dataPre_dict["type"] == "groupp":
        chatFlag, groupFlag, groupName = serverReply.groupChatting(data_dict, data_socket)
    # 断点续传探寻报文
    elif dataPre_dict["type"] == "respof":    
        usern = data_dict["Initiator_username"]
        Obj, i = serverReply.iteratingPool(usern)
        if Obj["onlineFlag"]:    
            sockUser2 = Obj["socket"]
            none = serverReply.testforfile(data_dict, sockUser2)
        else: pass
    # P2P语音聊天预处理
    elif dataPre_dict["type"] == "voicee":
        global addressList, messageList
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, True)
        s.bind(('', PORTUDP))

        while True:
            print(messageList)
            message, address = s.recvfrom(2048)
            message = message.decode()
            
            if len(addressList) < 2:
                addressList.append(address)
                messageList.append(message)
                print("add:", address)
            if len(addressList) == 2 and messageList[0] == messageList[1]:
                print("sending")
                break
        # 给两个用户发送对方的IP和port信息，转P2P通信
        s.sendto(str([addressList[0], "1"]).encode(), addressList[1])
        s.sendto(str([addressList[1], "1"]).encode(), addressList[0])
        s.close()
        # 清空
        addressList = []
        messageList = []


    else:
        print("Nothing. continue...")
        # print("0 accessFlag and chatFlag: ", accessFlag, chatFlag)
    return accessFlag, chatFlag, groupFlag, ObjectUser, groupName

# 消息转发
def linkandtransmition(data_socket, accessFlag, chatFlag, groupFlag):
    # 重新设计：和服务器连接之后，用户登录。
    # 在客户端，用户登录成功之后，返回的login报文将所有不在线用户、在线用户的信息返回。并且可以刷新来让服务器返回最新的用户信息
    # 服务器端：等待一个连接报文，即建立客户端和另外一个客户端在服务器内部的通信通道，如果不想继续，将线程关掉即可，没必要关socket

    # 线程关掉之后，继续那个刷新连接的循环（主循环）——然后再建立线程，关闭线程，建立关闭建立关闭。最后如果输入是退出，关闭socket。
    
    # 通信通道建立之后：
    # 如果对方已经在线，即数据库中对应的username已经登录(必然已经连接),则新建一个子线程用于双方通信
    # 如果对方并不在线，文字或文件发送到服务器后，暂存（设置过期时间redius数据库）
    # 服务器应该维护一个在线用户的列表：username、nickname和socket对应关系——（这里默认服务器内部的都是好友，可以通信的）
    # 同时维护一个待发送数据的数据结构，每次有用户登录时都要遍历这个列表，如果usename可以对应上，把离线的数据发送过去。
    global ServerUsersPool

    while(True):
        # 针对每一个已登录用户的外层大循环，用于登录（密码错误重新登录）注册，和不同用户文字chat、文件传输（在线or离线）等
        # 用户退出登录置accessFlag = True, 重新进入登录注册内循环。

        while(accessFlag or chatFlag):          
            # 用户登录或者注册成功后，选择操作（连接一个用户或群聊）后，退出该循环
            # 类型报头
            try:
                print("again.....")
                dataPre = data_socket.recv(BUFPRELEN)
                dataPre = dataPre.decode('utf-8')
                dataPre_dict = json.loads(dataPre)

                if dataPre_dict["type"] == "logout": # 如果退出登录
                    accessFlag = True # 下次将重新进入登录注册内循环
                    data = data_socket.recv(BUFLEN).decode('utf-8')
                    data_dict = json.loads(data)
                    shut_username = data_dict["username"]
                    print("shutname:", shut_username)
                    
                    serverReply.updateServerUsersPoolwhenLogOut(shut_username, data_socket) # 更新用户池中的数据, 并向客户端发送确认信息

                    print("Log out.")
                    continue # 退出第一次循环

                data = data_socket.recv(BUFLEN)
                # print("哈---------------------")
                # time.sleep(10)

                # print("\n-1 accessFlag and chatFlag: ", accessFlag, chatFlag)
                accessFlag, chatFlag, groupFlag, ObjectUser, groupname = accountProcessing(dataPre, data, data_socket, accessFlag, chatFlag, groupFlag)

                if ObjectUser != None: 
                    # 进入这个分支只有一个可能即：登录or注册成功且客户端已经选择了一个用户建立chat
                    # 即 accessFlag == false  chatFlag == false
                    if ObjectUser["onlineFlag"] == True:
                        # print(ObjectUser)
                        print("双方用户在线，建立新的聊天线程...")
                        # print("1 accessFlag and chatFlag: ", accessFlag, chatFlag)
                        break
                # print("2 accessFlag and chatFlag: ", accessFlag, chatFlag)
            except (ConnectionAbortedError, ConnectionResetError):
                # 将连接对象从监听列表去掉
                print("客户端与服务器端断开连接[0]")
                traceback.print_exc()
                data_socket.close()
                return     
            except Exception:
                print("连接断开，发生了其它异常[1]: ")
                traceback.print_exc()
                data_socket.close()
                return       

        User0 = data_socket
        print("User0:  ",User0)
        if groupFlag == False:  # 如果不是群聊
            User1 = ObjectUser["socket"]
            User1name = ObjectUser["username"]
            group = ''
            print("User1:  ",User1)
        else:                   # 如果是群聊
            User1 = None
            User1name = ''
            group = groupname

        # 文字聊天、文件传输（在线or离线）、群聊？、语音
        # trans1 = threading.Thread(target = transmitData, args = (User0, User1, chatFlag, BUFLEN))
        trans1 = MyThread(transmitData, args = (User0, User1, User1name, chatFlag, group, groupFlag, BUFLEN))
        # trans1.daemon = True
        trans1.start()
        # trans2 = threading.Thread(target = transmitData, args = (User1, User0, BUFLEN))
        # trans2.daemon = True
        # trans2.start()

        trans1.join()

        chatFlag, groupFlag = trans1.get_result() # 线程返回值

        print("线程：", trans1.is_alive())
        # trans2.join()


if __name__ == '__main__':
    # 实例化一个socket赋值给变量listen_socket, 参数AF_INET就是IP地址族 # 参数SOCK_STREAM就是TCP、参数SOCK_DGRAM就是UDP、参数SOCK_RAW是原始套接字，为TCP、UDP之外的协议提供接口
    listen_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    listen_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, True)  # 端口复用
    # listen_socket.setblocking(True) # 阻塞或非阻塞的设置
    listen_socket.bind((IP, PORT)) # IP设置为''为监听全部可能的IP地址 # 为这个socket绑定IP和端口，bind的对象必须是一个包含IP和端口元组

    # 使socket处于监听状态，等待客户端的请求，只有服务端能使用监听
    listen_socket.listen(16)  # 参数表示，最多接收10个等待连接的客户端
    print(f'Server: 服务启动成功，端口{PORT}，等待 Client 连接... ...')

    serverReply.initServerUsersPool() # 服务器刚启动时,用于ServerUsersPool初始化(从数据库读取用户资料)
    # Users = []
    while True:
        # 监听socket的accept方法，用来接收客户端的连接，如果没有客户端连接，就一直处于监听状态（阻塞状态）直到有客户端连接
        # 一旦客户段发起连接（TCP三次握手）accept方法就会返回一个元组，一个data_socket来传输数据，一个ipaddress包含IP和PORT
        # data_socket, ip_port = listen_socket.accept()
        # print(f'Server>>> 接受一个客户端{ip_port}连接... ...')
        # sub_threading = threading.Thread(target=dockingClient, args = (data_socket,))
        # sub_threading.start()
        
        # Users = []
        # while len(Users) != 2:
        data_socket, ip_port = listen_socket.accept()
        print(data_socket, ip_port)
        print("IP地址: ", data_socket.getpeername()[0])
        # Users.append(data_socket) # 可以不要这步，没登陆不统计

        # linkandtransmition(Users)
        # 创建线程用于接受客户端的登录注册操作
        accessFlag = True
        chatFlag = True
        groupFlag = False    # 是否加入群聊的标志
        clientThread = threading.Thread(target = linkandtransmition, args = (data_socket, accessFlag, chatFlag, groupFlag,))
        clientThread.start()

    listen_socket.close()
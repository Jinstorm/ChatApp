import json
import socket
import os
from user_info_util import user_util # user_util是UserUtil类的一个实例
from TCP_s1 import ServerUsersPool # 用户池
import time
BUFLEN = 1024
BUFPRELEN = 18
# 每次发送报文前先发送长度为18的报文头

# 缓存信息池
offlineInfoCachePool = []
'''
CacheInfo = {
    "username": username,
    "fromusername": sendusername,
    "fromnickname": sendnickname,
    "message": message # 字符串列表
    "file": file # 文件名列表
}
'''

# 群聊池
existingGroupChatPool = []
'''
groupchats = {
    "groupname": groupname,
    "groupmember": member[],
    "membernum": num
}
'''

def iteratingCachePool(usernameToChat):
    '''
    遍历用户池
    ServerSaved_Users = {
        "username": None,
        "nickname": None,
        "onlineFlag":False, 
        "socket": None
    } # 用户信息结构
    '''
    for i in range(len(offlineInfoCachePool)):
        if usernameToChat == offlineInfoCachePool[i]["username"]:
            return offlineInfoCachePool[i], i
    return False, -1

def updateUserOnline(data_dict, sockUser):
    '''
    更新用户在线信息
    
    update_data = {}
    update_data["type"] = "update"
    update_data[""] = account
    '''
    user = [] # 存储更新的用户信息
    for i in range(len(ServerUsersPool)):
        if ServerUsersPool[i]["onlineFlag"] == True:
            user.append((ServerUsersPool[i]["username"], "online"))
        else:
            user.append((ServerUsersPool[i]["username"], "offline"))

    preDataSend = {
        "type": "update"
    }
    preData = json.dumps(preDataSend)
    sockUser.send(preData.encode("utf-8"))

    update_data = {}
    update_data["type"] = "update"
    update_data["update_user"] = user
    print(user)
    update_data = json.dumps(update_data)
    sockUser.send(update_data.encode("utf-8"))
    print("已发送更新的用户在线信息.")






def iteratingPool(usernameToConnect):
    '''
    遍历用户池
    ServerSaved_Users = {
        "username": None,
        "nickname": None,
        "onlineFlag":False, 
        "socket": None
    } # 用户信息结构
    '''
    for i in range(len(ServerUsersPool)):
        if usernameToConnect == ServerUsersPool[i]["username"]:
            return ServerUsersPool[i], i
    return False, -1
def connectToUserOnline(data_dict, sockUser): # 在线不在线均可
    '''
    连接用户
    connect_data = {}
        connect_data["type"] = "connec"
        connect_data["connect_username"] = username
    '''
    connect_username = data_dict["connect_username"].strip()
    print("正在连接用户 %s ..." % (connect_username))
    ObjectUser, i = iteratingPool(connect_username)

    if ObjectUser == False:  # 用户不存在
        message = "User [%s] not founded." % (connect_username)
        code = "001"
        print("用户不存在.")
    else:       # 用户在线or下线, 准备chat
        if ObjectUser["onlineFlag"] == True: tag = "online"
        else: tag = "offline"
        message = "Object User %s is %s at present, the User-User connection is established anyway." % (connect_username, tag) # 在线or下线
        code = "000"
        print("找到目标用户.")

    preDataSend = {
        "type": "connec"
    }
    preData = json.dumps(preDataSend)
    sockUser.send(preData.encode("utf-8"))

    connectUser_data = {}
    connectUser_data["type"] = "connec"
    connectUser_data["code"] = code
    connectUser_data["message"] = message

    connectUser_data = json.dumps(connectUser_data)
    sockUser.send(connectUser_data.encode("utf-8"))

    if code == "000": return False, ObjectUser
    else: return True, None








def iteratingGroupChatPool(groupname):
    for i in range(len(existingGroupChatPool)):
        if groupname == existingGroupChatPool[i]["groupname"]:
            return existingGroupChatPool[i], i
    return None, -1

def groupChatting(data_dict, data_socket):
    groupname = data_dict["groupname"]
    username = data_dict["username"]
    Obj, i = iteratingGroupChatPool(groupname)
    # existingGroupChatPool = []
    '''
    groupchats = {
        "groupname": groupname,
        "groupmember": member[],
        "membernum": num
    }
    '''
    if Obj == None: # 当前群聊不存在，需要创建群聊
        member = []
        member.append( [username, data_socket] )
        num = 1
        group = {
            "groupname": groupname,
            "groupmember": member,
            "membernum": int(num)
        }
        existingGroupChatPool.append(group)

        # 发送创建成功的报文###############################
        code = "000"
        preDataSend = {
            "type": "groupp"
        }
        preData = json.dumps(preDataSend)
        data_socket.send(preData.encode("utf-8"))

        group_data = {}
        group_data["type"] = "groupp"
        group_data["code"] = code
        group_data["groupname"] = groupname
        group_data["message"] = "New chat group [%s] has been created successfully.\nCurrent member number:%d, group member:%s" % (groupname, num, username)

        group_data = json.dumps(group_data)
        data_socket.send(group_data.encode("utf-8"))
    else:
        existingGroupChatPool[i]["groupmember"].append( [username, data_socket] )
        existingGroupChatPool[i]["membernum"] += 1

        # 发送加入成功的报文##############################
        # Obj["groupmember"].append( [username, data_socket] )
        # Obj["membernum"] += 1
        printMem = []
        for j in existingGroupChatPool[i]["groupmember"]:
            printMem.append(j[0])
        printMem = ' '.join(printMem) # 群聊成员的username信息

        code = "000"
        preDataSend = {
            "type": "groupp"
        }
        preData = json.dumps(preDataSend)
        data_socket.send(preData.encode("utf-8"))

        group_data = {}
        group_data["type"] = "groupp"
        group_data["code"] = code
        group_data["groupname"] = groupname
        group_data["message"] = "Join the chat group [%s] successfully.\nCurrent member number:%d, group member:%s" % (groupname, Obj["membernum"], printMem)

        group_data = json.dumps(group_data)
        data_socket.send(group_data.encode("utf-8"))

    return False, True, groupname













def transmitFile(userFrom, userTo, User2name):
    '''
    接收大文件并转发
    prehead structure:
        prehead = {
            "type": "file",
            "length": len(head_info)
        }
    '''

    ### 转发文件 ###
    Obj, i = iteratingPool(User2name)
    userTo = Obj["socket"]
    # 对方不在线，对离线文件进行存储，对方上线时由login函数的功能进行转发
    if Obj["onlineFlag"] == False: 

        # 接收文件
        headLength = userFrom.recv(30)  #  接受报头的长度 prehead
        headLength_dict = json.loads(headLength.decode('utf-8')) # 解码并反序列化
        headinfoLength = headLength_dict["length"]              # 解析得到报头信息的长度

        headInfo = userFrom.recv(headinfoLength)
        headInfo_dict = json.loads(headInfo.decode('utf-8')) 
        filename = recv_file(headInfo_dict, userFrom)

        # 存储文件
        data = {}
        data["type"] = "chat"
        preDataSend = {
            "type": "chattt"
        }
        preData = json.dumps(preDataSend)
        userFrom.send(preData.encode("utf-8"))

        data["message"] = "Sorry, the object user is offline at present. But the file will be still passed to him/her." # Message is passed to the object user though he/she is offline.
        data["nickname"] = "[Server prompt]"
        data = json.dumps(data)
        userFrom.send(data.encode("utf-8"))

        messageListinCache = []
        filenameList = []
        CacheInfo = {
            "username": User2name,
            "fromusername": "",
            "fromnickname": "",
            "message": messageListinCache,
            "file": filenameList
        }
        Obj2, j = iteratingCachePool(User2name)
        if j == -1:         # 目标用户不在表中，新建一条记录
            filenameList.append(filename) 
            offlineInfoCachePool.append(CacheInfo)
        else: 
            offlineInfoCachePool[j]["file"].append(filename) # 增加message待发信息

    else:
        # 不存储，直接转发文件（对方在线时）
        # 接收文件
        headLength = userFrom.recv(30)  #  接受报头的长度 prehead
        headLength_dict = json.loads(headLength.decode('utf-8')) # 解码并反序列化
        headinfoLength = headLength_dict["length"]              # 解析得到报头信息的长度

        headInfo = userFrom.recv(headinfoLength)
        headInfo_dict = json.loads(headInfo.decode('utf-8')) 
        ReceiveandTransmitNow(headInfo_dict, userFrom, userTo)


def ReceiveandTransmitNow(headInfo_dict, userFrom, userTo):
    '''
    直接转发
    '''
    filename = headInfo_dict['filename']
    filesize_b = headInfo_dict['filesize_bytes']
    trans_len = 0
    trans_mesg = b''

    # 先给目标用户发送提示信息
    preDataSend = {
        "type": "fileee"
    }
    preData = json.dumps(preDataSend)
    userTo.send(preData.encode("utf-8")) # 发送预处理报文: 18字节

    head_info_len, head_info = pretreatFileinDirectTransmition(filename, filesize_b, headInfo_dict["type"]) 
    userTo.send(head_info_len.encode('utf-8'))  # 这里是30个字节(发送的是报头长度)
    userTo.send(head_info.encode('utf-8'))  # 发送报头的内容(包括报文类型file、文件名和文件大小)

    # 接收并转发文件（完整文件or断点续传的文件）
    while trans_len < filesize_b:
        if filesize_b - trans_len > BUFLEN:
            trans_mesg = userFrom.recv(BUFLEN)
            trans_len += len(trans_mesg)
            # 直接转发
            userTo.send(trans_mesg)

        else:
            trans_mesg = userFrom.recv(filesize_b - trans_len)
            trans_len += len(trans_mesg)
            userTo.send(trans_mesg)

    print('%s 传输完成' % filename)



def recv_file(headInfo_dict, userFrom):
    '''
    接收大文件,返回文件名
    headinfo structure:
        head_dir = {
            "type": "file",
            "filename": 'new' + filename,
            "filesize_bytes": filesize_bytes,
        }
    '''
    filename = headInfo_dict['filename']
    filesize_b = headInfo_dict['filesize_bytes']
    recv_len = 0
    recv_mesg = b''
    f = open(filename, 'wb')
    while recv_len < filesize_b:
        if filesize_b - recv_len > BUFLEN:
            recv_mesg = userFrom.recv(BUFLEN)
            recv_len += len(recv_mesg)
            f.write(recv_mesg)
        else:
            recv_mesg = userFrom.recv(filesize_b - recv_len)
            recv_len += len(recv_mesg)
            f.write(recv_mesg)

    f.close()
    print('%s 传输完成' % filename)
    return filename


# 用于直接转发
def pretreatFileinDirectTransmition(filename, filesize_b, type):
    '''
    对报头进行打包, 发送文件大小的预处理报文
    '''
    filesize_bytes = filesize_b # 字节为单位
    head_dir = {
        "type": type,   # 可能是：file，也可能是断点续传的：filecontinuation
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





def pretreatFile(filename):
    '''
    对报头进行打包, 发送文件大小的预处理报文
    '''
    filesize_bytes = os.path.getsize(filename) # 字节为单位
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

def sendFiletoClient(sock, filename):
    '''
    发送文件内容
    '''
    with open(filename, 'rb') as f:
        sock.sendall(f.read())
    print('%s 发送成功' % filename)








def queryForFileSituation(data_dict, sockUser1, sockUser2, User2name):
    # targetusername = data_dict["targetname"]
    # print(targetusername)
    Obj, i = iteratingPool(User2name)
    print("Obj[onlineFlag]:", Obj["onlineFlag"])

    if Obj["onlineFlag"] == False:
        # 对方此时不在线，返回-1，使用离线文件传输
        print("Object user is offline at present.")
        preDataSend = {
            "type": "respof"
        }
        preData = json.dumps(preDataSend)

        response = {}
        response["type"] = "respof"
        response["has_size"] = -1
        response["origin_size"] = -1
        print("has_size, origin_size: ", -1, -1)
        respo_data = json.dumps(response)

        sockUser1.send(preData.encode("utf-8")) # 发送预处理报文-18字节
        sockUser1.send(respo_data.encode("utf-8")) # 发送response

    else:
        sockUser2 = Obj["socket"]
        preDataSend = {
            "type": "queryf"
        }
        preData = json.dumps(preDataSend)
        sockUser2.send(preData.encode("utf-8")) # 发送预处理报文-18字节
        sockUser2.send(json.dumps(data_dict).encode("utf-8")) # 转发

        # print("???????????----------")

        # try:
        #     dataPre = sockUser2.recv(BUFPRELEN)
        #     data = sockUser2.recv(BUFLEN)
        #     dataPre = dataPre.decode('utf-8')
        #     dataPre_dict = json.loads(dataPre)

        #     print(dataPre_dict)
        #     dataPre = json.dumps(dataPre_dict).encode("utf-8")

        # except (ConnectionAbortedError, ConnectionResetError):
        #     # 将连接对象从监听列表去掉
        #     print("客户端与服务器端断开连接--0")
        # except Exception:
        #     # print("OSError occurred")
        #     print("客户端发生了其它异常--0: ")
        # print("Okkkkkkkkkkkkkkkkkkkkkkkkkkkk?")
        # # sockUser1.send(dataPre) # 发送预处理报文-18字节
        # # sockUser1.send(data)
        # time.sleep(10)
    return True


def testforfile(data_dict, sockUser2):
    # time.sleep(0.5)
    '''
    response["type"] = "respof"
                    response["has_size"] = 0
                    response["origin_size"] = origin_size
                    response["Initiator_username"] = data_dict["username"]
    '''
    preDataSend = {
        "type": "respof"
    }
    preData = json.dumps(preDataSend)
    
    size1 = data_dict["has_size"]
    size2 = data_dict["origin_size"]
    
    data_d = {}
    data_d["type"] = "respof"
    data_d["has_size"] = size1
    data_d["origin_size"] = size2
    
    data = json.dumps(data_d)
    print(data_d)
    sockUser2.send(preData.encode("utf-8")) # 发送预处理报文-18字节
    sockUser2.send(data.encode("utf-8"))
    print("send success!")
    return True






# 聊天逻辑(拆开数据包看看类型字段，如果是聊天数据包，再次封装然后转发)
def chat(data_dict, userFrom, userTo, User2name, groupname, groupFlag):
    """
    :param data_dict: 客户端的请求消息
    :param userFrom: 发送方
    :param userTo: 接收方
    """
    message = data_dict["message"].strip()
    nickname = data_dict["nickname"].strip()
    username = data_dict["username"].strip()

    ### 1v1聊天 ###
    if groupFlag == False: 
        if(message == "END"):
            print("Chat ends.")
            # userFrom.close()
            # userTo.close()
            return False # 表示当前聊天结束，需要退出接收消息的阻塞循环

        data = {}
        data["type"] = "chat"
        data["message"] = message
        data["nickname"] = nickname
        
        preDataSend = {
            "type": "chattt"
        }
        preData = json.dumps(preDataSend)

        # 对方不在线时：（目前的处理是：给发送端发送提示信息）
        Obj, i = iteratingPool(User2name)
        if Obj["onlineFlag"] == False:
            # print("Sorry, the object user is offline at present.")
            userFrom.send(preData.encode("utf-8"))
            data["message"] = "Sorry, the object user is offline at present. But the message will be still passed to him/her." # Message is passed to the object user though he/she is offline.
            data["nickname"] = "[Server prompt]"
            data = json.dumps(data)
            userFrom.send(data.encode("utf-8"))

            messageListinCache = []
            filename = []
            CacheInfo = {
                "username": User2name,
                "fromusername": username,
                "fromnickname": nickname,
                "message": messageListinCache,
                "file": filename
            }
            Obj2, j = iteratingCachePool(User2name)
            if j == -1:         # 目标用户不在表中，新建一条记录
                messageListinCache.append(message) 
                offlineInfoCachePool.append(CacheInfo)
            else: 
                offlineInfoCachePool[j]["message"].append(message) # 增加message待发信息
            

        # 对方在线时：直接发送即可
        # 这里还要考虑到对方忽然上线, 故需要使用 userTo = Obj["socket"]
        else:
            userTo = Obj["socket"]
            data = json.dumps(data)
            userTo.send(preData.encode("utf-8"))
            userTo.send(data.encode("utf-8"))
        return True
    
    ### 群聊 ###
    elif groupFlag == True: 
        Obj, i = iteratingGroupChatPool(groupname)
        # existingGroupChatPool = []
        '''
        groupchats = {
            "groupname": groupname,
            "groupmember": member[],
            "membernum": num
        }
        '''
        if(message == "END"):
            print("Chat ends.")
            # 删除用户信息
            existingGroupChatPool[i]["groupmember"].remove([username, userFrom])
            existingGroupChatPool[i]["membernum"] -= 1
            return False # 表示当前聊天结束，需要退出接收消息的阻塞循环
        data = {}
        data["type"] = "chat"
        data["message"] = message
        data["nickname"] = nickname
        
        preDataSend = {
            "type": "chattt"
        }
        preData = json.dumps(preDataSend)
        data = json.dumps(data)
        
        # existingGroupChatPool = []
        '''
        groupchats = {
            "groupname": groupname,
            "groupmember": member[[username, data_socket], ...],
            "membernum": num
        }
        '''
        for objectiveUser in Obj["groupmember"]:
            print("name:", objectiveUser[0])
            if username != objectiveUser[0]:
                objectiveUser[1].send(preData.encode("utf-8"))
                objectiveUser[1].send(data.encode("utf-8"))

        return True

    # # 遍历所有的连接对象，群发消息
    # for user in self.users.keys():
    #     data = {}
    #     data["type"] = "chat"
    #     # 获取当前发送消息客户端的昵称
    #     nickname = self.users[self]
    #     data["nickname"] = nickname
    #     # "isMy"键默认为no
    #     data["isMy"] = "no"
    #     # 如果遍历的对象与发消息客户端是同一个，则将isMy字段设为yes, 便于前端用来判断展示不同的字体样式
    #     if user == self:
    #         data["isMy"] = "yes"
    #     data["message"] = message
    #     data = json.dumps(data)
    #     user.sendLine(data.encode("utf-8"))










# 登录逻辑
def login(data_dict, user):
    """
    :param data_dict: 客户端的请求消息
    :param user: 登录请求方
    """
    username = data_dict["username"].strip()
    password = data_dict["password"].strip()
    # 服务器端的响应消息
    data = {}
    # 账号密码不能为空
    if username and password:
        code, msg, nickname = login_check(username, password)
    elif not username:
        code = "003"
        msg = "登录用户名不能为空"
    elif not password:
        code = "004"
        msg = "登录密码不能为空"
    # # 登录成功，将连接对象以及昵称加到users中，便于后续遍历发送消息
    # if code == "000":
    #     # 在全局变量users中新增用户信息
    #     self.users[self] = nickname
    #     data["nickname"] = nickname
    # code = "000"
    # msg = "hello"
    data["type"] = "login"
    data["code"] = code
    data["msg"] = msg
    data["username"] = username
    data["nickname"] = nickname
    data = json.dumps(data)
    preDataSend = {
        "type": "signin"
    }
    preData = json.dumps(preDataSend)
    user.send(preData.encode("utf-8"))
    user.send(data.encode("utf-8"))

    time.sleep(0.5)

    if code == "000": 
        '''
        如果有离线消息和离线文件，发送即可
        '''
        Object, i = iteratingPool(username)
        if i == -1:
            # 将当前用户添加到用户池中
            ServerSaved_User = {}
            ServerSaved_User["username"] =  username
            ServerSaved_User["nickname"] =  nickname
            ServerSaved_User["onlineFlag"] = True
            ServerSaved_User["socket"] =  user
            ServerUsersPool.append(ServerSaved_User)
        else:
            ServerUsersPool[i]["onlineFlag"] = True
            ServerUsersPool[i]["socket"] = user
        
        # 给刚刚登录的用户发送存储的离线信息——应该要所有其他用户给它发的离线信息
        Obj2, j = iteratingCachePool(username)
        if j == -1:         # 目标用户不在表中，没有缓存消息或文件需要发送
            return False
        
        if Obj2["message"] != []:
            # 转发文字消息
            preDataSend = {
                "type": "signin"
            }
            preData = json.dumps(preDataSend)
            user.send(preData.encode("utf-8"))

            data = {}
            data["type"] = "chat"
            data["message"] = "\n\t".join(offlineInfoCachePool[j]["message"])
            data["nickname"] = offlineInfoCachePool[j]["fromnickname"]
            # print("需要发送缓存信息，且前期信息存储的内容也要增加，要增加发送人的Username和nickname")
            data = json.dumps(data)
            user.send(data.encode("utf-8"))
            print("%s的离线消息已发送给%s." % (offlineInfoCachePool[j]["fromnickname"], username))

            # 清空待发送信息
            offlineInfoCachePool[j]["message"] = []
        

        if Obj2["file"] != []: 
            # 转发文件（对方在线时）
            for k in range(len(Obj2["file"])):
                time.sleep(0.5)         # ############## 不知道为什么就是可能要先停顿一下？？？

                filename = Obj2["file"][k]
                userTo = user
                preDataSend = {
                    "type": "fileee"
                }
                preData = json.dumps(preDataSend)
                userTo.send(preData.encode("utf-8"))

                head_info_len, head_info = pretreatFile(filename) #发送预处理报文-18字节
                userTo.send(head_info_len.encode('utf-8'))  # 这里是30个字节(发送报头长度)
                userTo.send(head_info.encode('utf-8'))  # 发送报头的内容(包括报文类型file、文件名和文件大小)
                # 发送文件内容
                sendFiletoClient(userTo, filename) # socket和文件名(包括扩展名)

            print("离线文件已发送给%s." % username)
            offlineInfoCachePool[j]["file"] = []

        return False
    else: return True

# 登录校验逻辑
def login_check(username, password):
    print("checking username and password...")
    # 通过用户名到数据库获取用户信息
    user_info = user_util.user_check(username)
    # 未查到该用户信息，代表未注册
    if len(user_info) == 0:
        data = ("001", "账号[%s]未注册, 请先注册!" % username, None)
    # 密码错误
    elif password != user_info[0][1]:
        data = ("002", "密码有误，请重新输入!", None)
    # 正常登录
    else:
        # 获取昵称
        nickname = user_info[0][2]
        data = ("000", "账号[%s]登录成功!" % username, nickname)
    return data







# 注册逻辑
def register(data_dict, user):
    """
    :param data_dict: 客户端的请求消息
    :param user: 注册请求方
    """
    username = data_dict["username"].strip()
    password = data_dict["password"].strip()
    nickname = data_dict["nickname"].strip()
    # 服务器端的响应消息
    data = {}
    # username、password、nickname者均不为空才能加入注册校验
    if username and password and nickname:
        code, msg = register_check(username, password, nickname)
    elif not username:
        code = "002"
        msg = "注册账号不能为空"
    elif not password:
        code = "003"
        msg = "注册密码不能为空"
    elif not nickname:
        code = "004"
        msg = "注册昵称不能为空"
    # if code == "000":
    #     self.users[self] = nickname
    #     data["nickname"] = nickname
    # code = "000"
    # msg = "hello"
    data["type"] = "register"
    data["code"] = code
    data["msg"] = msg
    data["nickname"] = nickname
    data = json.dumps(data)
    preDataSend = {
        "type": "signup"
    }
    preData = json.dumps(preDataSend)
    user.send(preData.encode("utf-8"))
    user.send(data.encode("utf-8"))

    if code == "000": 
        Object, i = iteratingPool(username)
        if i == -1:
            # 将当前用户添加到用户池中
            ServerSaved_User = {}
            ServerSaved_User["username"] =  username
            ServerSaved_User["nickname"] =  nickname
            ServerSaved_User["onlineFlag"] = True
            ServerSaved_User["socket"] =  user
            ServerUsersPool.append(ServerSaved_User)
        else:
            ServerUsersPool[i]["onlineFlag"] = True
            ServerUsersPool[i]["socket"] = user
        return False
    else: return True

# 注册校验
def register_check(username, password, nickname):
    user_info = user_util.user_check(username)
    if len(user_info) > 0:
        data = ("001", "账号[%s]已被注册过" % user_info)
    else:
        user_util.user_insert(username, password, nickname)
        data = ("000", "账号[%s]注册成功，即将进入聊天页面" % username)
    return data


def initServerUsersPool():
    '''
    初始化用户池
    '''
    res = user_util.user_wrapRecords()
    for i in range(len(res)):
        ServerSaved_User = {}
        ServerSaved_User["username"] =  res[i][0]
        ServerSaved_User["nickname"] =  res[i][1]
        ServerSaved_User["onlineFlag"] = False
        ServerSaved_User["socket"] =  None
        ServerUsersPool.append(ServerSaved_User)

def updateServerUsersPoolwhenLogOut(shut_username, data_socket):
    '''
    有用户退出登录时更新用户池
    '''
    Object, i = iteratingPool(shut_username)
    print(len(ServerUsersPool), i,  ServerUsersPool[i]["username"])
    ServerUsersPool[i]["onlineFlag"] = False
    ServerUsersPool[i]["socket"] = None
    
    preDataSend = {
        "type": "logout"
    }
    preData = json.dumps(preDataSend)
    data_socket.send(preData.encode("utf-8")) # 通知客户端已经成功登出
服务器程序文件： TCP_s1.py  serverReply.py  mysql_util.py  user_info_util.py
其中 TCP_s1.py 依赖于其他三者才能运行，且此服务器程序是基于MySQL数据库的。
TCP_s1.py——主程序
serverReply.py——重要的函数
mysql_util.py  user_info_util.py——数据库相关操作的类和函数

客户端程序文件：TCP_c1.py  progressbar.py
TCP_c1.py——主程序
progressbar.py——进度条展示函数
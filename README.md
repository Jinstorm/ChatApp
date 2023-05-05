服务器程序文件： 
- `TCP_s1.py`：主程序，依赖于另外3个py类和函数封装文件才能运行，且此服务器程序是基于MySQL数据库的。
- `serverReply.py`：重要的函数方法
- `mysql_util.py`，`user_info_util.py`：数据库相关操作的类和函数

客户端程序文件：
- `TCP_c1.py`：主程序
- `progressbar.py`：进度条展示函数

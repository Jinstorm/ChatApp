import mysql_util

class UserUtil:

    def __init__(self, host, port, db, user, passwd, charset="utf8"):
        self.mysql = mysql_util.MysqlTool(host, port, db, user, passwd, charset)

    def user_check(self, username):
        check_sql = "SELECT username,password,nickname FROM CLIENT WHERE username = '%s'" % username
        self.mysql.connect()
        user_info = self.mysql.get_all(check_sql)
        self.mysql.close()
        print("User record founded: ", user_info)
        return user_info

    def user_insert(self, username, passwd, nickname):
        insert_sql = "INSERT INTO CLIENT(username,password,nickname) VALUES('%s','%s','%s')" % (username, passwd, nickname)
        self.mysql.connect()
        self.mysql.insert(insert_sql)
        self.mysql.close()
        print("Insertion completed for ", username)
    
    def user_wrapRecords(self):
        group_sql = "SELECT username,nickname FROM CLIENT"
        self.mysql.connect()
        user_info = self.mysql.get_all(group_sql)
        self.mysql.close()
        return user_info


user_util = UserUtil(host="127.0.0.1",port=3306,user='root',passwd='123456',db='db_test',charset='utf8') # ("127.0.0.1", 3306, "test", "root", "admin")
# MysqlTool(host="127.0.0.1",port=3306,user='root',passwd='123456',db='db_test',charset='utf8')

if __name__ == "__main__":
    print(user_util.user_check("username_test"))
    user_util.user_insert("username_test2", "pwd", "nickname")
    print(user_util.user_check("username_test2"))
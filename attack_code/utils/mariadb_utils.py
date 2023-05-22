import mariadb
import random
import string
import subprocess
import os
import time

tablespaces_path = "/var/lib/mysql/"

class MariaDBController:
    def __init__(self, db : str):
        self.db_name = db
        self.db_path = tablespaces_path + db + "/"
        self.conn = mariadb.connect(user="root", host="localhost", database=db)
        self.cur = self.conn.cursor()
        self.old_edit_time = None
        self.backupdict = dict()

    def __flush_and_wait_for_change(self, tablename):
        self.flush_table(tablename)
        max_sleeps = 20
        sleeps = 0
        while os.path.getmtime(self.db_path + tablename + ".ibd") == self.old_edit_time:
            time.sleep(0.1)
            sleeps += 1
            if sleeps > max_sleeps:
                print("max sleeps")
                time.sleep(10)
                break
        if sleeps > 0:
            print("done sleeping")
        self.old_edit_time = os.path.getmtime(self.db_path + tablename + ".ibd")
        self.cur.execute("unlock tables")

    def drop_table(self, tablename):
        self.cur.execute("drop table if exists " + tablename)
        self.conn.commit()

    def backup_mariadb(self, backup_key="default"):
        self._stop_mariadb()
        subprocess.check_output(["rm", "-rf", "/var/lib/mysql.tmp" + backup_key])
        subprocess.check_output(["cp", "-r", "-p", tablespaces_path, "/var/lib/mysql.tmp" + backup_key])
        self._start_mariadb()

    def restore_mariadb(self, backup_key="default"):
        self._stop_mariadb()
        subprocess.check_output(["rm", "-rf", tablespaces_path])
        subprocess.check_output(["cp", "-r", "-p", "/var/lib/mysql.tmp" + backup_key, tablespaces_path])
        self._start_mariadb()

    def create_basic_table(self, tablename, varchar_len=100, compressed=False, encrypted=False):
        compressed_str = "1" if compressed else "0"
        encrypted_str = "YES" if encrypted else "NO"
        self.cur.execute("create table " + tablename + " (id INT not null, data VARCHAR(" + str(varchar_len) +
                "), primary key(id)) ENGINE=InnoDB PAGE_COMPRESSED=" + compressed_str + " ENCRYPTED=" + encrypted_str)
        self.conn.commit()
        time.sleep(2)
        self.old_edit_time = os.path.getmtime(self.db_path + tablename + ".ibd")

    def create_text_table(self, tablename, text_len, compressed=False, encrypted=False):
        compressed_str = "1" if compressed else "0"
        encrypted_str = "YES" if encrypted else "NO"
        self.cur.execute("create table " + tablename + " (id INT, data TEXT(" + str(text_len) +
                ")) ENGINE=InnoDB PAGE_COMPRESSED=" + compressed_str + " ENCRYPTED=" + encrypted_str)
        self.conn.commit()

    def create_mediumtext_table(self, tablename, compressed=False, encrypted=False):
        compressed_str = "1" if compressed else "0"
        encrypted_str = "YES" if encrypted else "NO"
        self.cur.execute("create table " + tablename + " (id INT, data MEDIUMTEXT) " +
                "ENGINE=InnoDB PAGE_COMPRESSED=" + compressed_str + " ENCRYPTED=" + encrypted_str)
        self.conn.commit()

    def create_longtext_table(self, tablename, compressed=False, encrypted=False):
        compressed_str = "1" if compressed else "0"
        encrypted_str = "YES" if encrypted else "NO"
        self.cur.execute("create table " + tablename + " (id INT, data LONGTEXT) " +
                "ENGINE=InnoDB PAGE_COMPRESSED=" + compressed_str + " ENCRYPTED=" + encrypted_str)
        self.conn.commit()

    def get_table_size(self, tablename, verbose=False):
        table_path = self.db_path + tablename + ".ibd"
        table_size = int(subprocess.check_output(["ls", "-s", "--block-size=1", table_path]).split()[0])
            print("Size of table " + tablename + ": " + str(table_size))
        return table_size

    def insert_row(self, tablename : str, idx : int, data : str):
        self.cur.execute("insert into " + tablename + " (id, data) values (?, ?)", (idx, data))
        self.conn.commit()
        self.__flush_and_wait_for_change(tablename)

    def update_row(self, tablename : str, idx : int, data : str):
        self.cur.execute("update " + tablename + " set data=? where id=?", (data, idx))
        self.conn.commit()
        self.__flush_and_wait_for_change(tablename)

    def delete_row(self, tablename : str, idx : int):
        self.cur.execute("delete from " + tablename + " where id=" + str(idx))
        self.conn.commit()
        self.__flush_and_wait_for_change(tablename)

    def optimize_table(self, tablename : str):
        self.cur.execute("optimize table " + tablename)
        status = False
        result = []
        for line in self.cur:
            result.append(line)
            if line[2] == 'status':
                status = line[3] == 'OK'
        if not status: 
            print("OPTIMIZE TABLE FAILED!")
            for line in result:
                print(line)
        return status

    def flush_table(self, tablename : str):
        self.cur.execute("flush tables " + tablename + " with read lock");

    def _stop_mariadb(self):
        subprocess.check_output(["systemctl", "stop", "mariadb"])
        self.cur = None
        self.conn = None

    def _start_mariadb(self):
        subprocess.check_output(["systemctl", "start", "mariadb"])
        self.conn = mariadb.connect(user="root", host="localhost", database=self.db_name)
        self.cur = self.conn.cursor()

def get_filler_str(data_len : int):
    return ''.join(
            random.choices(
                string.ascii_uppercase + string.ascii_lowercase + string.digits + string.punctuation,
                k=data_len))

def get_compressible_str(data_len : int, char = 'a'):
    return ''.join([char for _ in range(data_len)])

def init_words():
    global words
    words = []
    with open('../res/words.txt') as f:
        for line in f:
            word = line.strip()     
            if len(word) > 2 and len(word) < 20:
                words.append(word)

def get_random_word():
    global words
    return random.choice(words)


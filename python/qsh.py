# -*- coding: utf-8 -*-
__author__ = 'qiqi'

import sys

reload(sys)
sys.setdefaultencoding('utf8')

import socket
import os
import re
import select
import time
import paramiko
import struct
import fcntl
import textwrap
import getpass
import fnmatch
import readline
import datetime
from multiprocessing import Pool


try:
    import termios
    import tty
except ImportError:
    print '\033[1;31mOnly UnixLike supported.\033[0m'
    time.sleep(3)
    sys.exit()


# qiqi import
import getpass
import signal

from sqlalchemy import create_engine,MetaData
from sqlalchemy.orm import sessionmaker
SQLALCHEMY_DATABASE_URI = 'mysql://root:root@10.249.6.30:3306/cmdb_local?charset=utf8'
class Sql_helper():
    url=''
    Seeesion=''
    def __init__(self):
        self.url=''

    def Connect(self,_url):
        self.url=_url
        engine = create_engine(self.url, encoding='utf-8', echo=False)
        # DB_Session = sessionmaker(bind=engine)
        # self.Seeesion = DB_Session()
        metadata = MetaData(bind=engine, reflect=True)
        self.Seeesion = engine.connect()

    def Disconnect(self):
        self.Seeesion.close()
        self.Seeesion=''

    def checkReconnect(self):
        if not self.Seeesion:
            engine = create_engine(self.url, echo=False)
            DB_Session = sessionmaker(bind=engine)
            self.Seeesion = DB_Session()

    def executeCmd(self,args,mode=False):
        try:
            self.checkReconnect()
            if mode:
                return self.Seeesion.execute(args)
            else:
                return self.Seeesion.execute(args).first()
        except Exception,e:
            return []


LOGIN_NAME = getpass.getuser()
COLLECTS=[]
# qiqi ?
#LOGIN_NAME = 'qiqi'

def color_print(msg, color='blue'):
    """Print colorful string."""
    color_msg = {'blue': '\033[1;36m%s\033[0m',
                 'green': '\033[1;32m%s\033[0m',
                 'red': '\033[1;31m%s\033[0m'}

    print color_msg.get(color, 'blue') % msg


def color_print_exit(msg, color='red'):
    """Print colorful string and exit."""
    color_print(msg, color=color)
    time.sleep(2)
    sys.exit()

def verify_connect(username, part_ip):
    try:
        host_id = get_host_id(part_ip)
        if not host_id:
            color_print('没有找到该服务器！', 'red')
            return False
        hosts = get_user_host(username)
        if not hosts:
            color_print('没有权限登录此服务器！', 'red')
            return False
    except ServerError, e:
        color_print(e, 'red')
        return False
    ip_matched = ""
    for ip_info in hosts:
        if host_id == ip_info and host_id:
            ip_matched = part_ip
            break
    if len(ip_matched) > 0:
        login_server(ip_matched, username)
    else:
        color_print('没有权限！', 'red')

def get_win_size():
    """This function use to get the size of the windows!"""
    if 'TIOCGWINSZ' in dir(termios):
        TIOCGWINSZ = termios.TIOCGWINSZ
    else:
        TIOCGWINSZ = 1074295912L  # Assume
    s = struct.pack('HHHH', 0, 0, 0, 0)
    x = fcntl.ioctl(sys.stdout.fileno(), TIOCGWINSZ, s)
    return struct.unpack('HHHH', x)[0:2]


def set_win_size(sig, data):
    """This function use to set the window size of the terminal!"""
    try:
        win_size = get_win_size()
        channel.resize_pty(height=win_size[0], width=win_size[1])
    except:
        pass



def log_record(username, host):
    LOG_DIR = "/tmp/log/"
    """Logging user command and output."""
    connect_log_dir = os.path.join(LOG_DIR, 'connect')
    timestamp_start = int(time.time())
    today = time.strftime('%Y%m%d', time.localtime(timestamp_start))
    time_now = time.strftime('%H%M%S', time.localtime(timestamp_start))
    today_connect_log_dir = os.path.join(connect_log_dir, today)
    log_filename = '%s_%s_%s.log' % (username, host, time_now)
    log_file_path = os.path.join(today_connect_log_dir, log_filename)
    dept_name = 'qiqi'
    pid = os.getpid()
    pts = os.popen("ps axu | awk '$2==%s{ print $7 }'" % pid).read().strip()
    ip_list = os.popen("who | awk '$2==\"%s\"{ print $5 }'" % pts).read().strip('()\n')

    if not os.path.isdir(today_connect_log_dir):
        try:
            os.makedirs(today_connect_log_dir)
            os.chmod(today_connect_log_dir, 0777)
        except OSError:
            raise ServerError('Create %s failed, Please modify %s permission.' % (today_connect_log_dir, connect_log_dir))

    try:
        log_file = open(log_file_path, 'a')
    except IOError:
        raise ServerError('Create logfile failed, Please modify %s permission.' % today_connect_log_dir)

    # log = Log(user=username, host=host, remote_ip=ip_list, dept_name=dept_name,
    #           log_path=log_file_path, start_time=datetime.datetime.now(), pid=pid)
    log_file.write('Starttime is %s\n' % datetime.datetime.now())
    # log.save()
    return log_file

def posix_shell(chan, username, host):
    """
    Use paramiko channel connect server interactive.
    """
    log_file = log_record(username, host)
    old_tty = termios.tcgetattr(sys.stdin)
    try:
        tty.setraw(sys.stdin.fileno())
        tty.setcbreak(sys.stdin.fileno())
        chan.settimeout(0.0)

        while True:
            try:
                r, w, e = select.select([chan, sys.stdin], [], [])
            except:
                pass

            if chan in r:
                try:
                    x = chan.recv(10240)
                    if len(x) == 0:
                        break
                    sys.stdout.write(x)
                    sys.stdout.flush()
                    log_file.write(x)
                    log_file.flush()
                except socket.timeout:
                    pass

            if sys.stdin in r:
                x = os.read(sys.stdin.fileno(), 1)
                if len(x) == 0:
                    break
                chan.send(x)

    finally:
        termios.tcsetattr(sys.stdin, termios.TCSADRAIN, old_tty)
        log_file.write('Endtime is %s' % datetime.datetime.now())
        log_file.close()
        # log.is_finished = True
        # log.log_finished = False
        # log.end_time = datetime.datetime.now()
        # log.save()
        print_prompt()

def connect(username, password, host, port, login_name):
    """
    Connect server.
    """
    ps1 = "PS1='[\u@%s \W]\$ ' && TERM=xterm && export TERM\n" % host
    login_msg = "clear;echo -e '\\033[32mLogin %s done. Enjoy it.\\033[0m'\n" % host

    # Make a ssh connection
    ssh = paramiko.SSHClient()
    # ssh.load_system_host_keys()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    try:
        ssh.connect(host, port=port, username=username, password=password, compress=True)
        # ssh.connect(username=username, password=password)
    except paramiko.ssh_exception.AuthenticationException, paramiko.ssh_exception.SSHException:
        raise ServerError('Authentication Error.')
    except socket.error:
        raise ServerError('Connect SSH Socket Port Error, Please Correct it.')

    # Make a channel and set windows size
    global channel
    win_size = get_win_size()
    channel = ssh.invoke_shell(height=win_size[0], width=win_size[1])
    try:
        signal.signal(signal.SIGWINCH, set_win_size)
    except:
        pass

    # Set PS1 and msg it
    channel.send(ps1)
    channel.send(login_msg)

    # Make ssh interactive tunnel
    posix_shell(channel, login_name, host)

    # Shutdown channel socket
    channel.close()
    ssh.close()

def login_server(ip, user):
    print "正在登陆: %s" % (ip)
    print "用户名: %s" % (user)
    # password = getpass.getpass()
    connect(user, "anjuke_88", ip , 22, LOGIN_NAME)

def print_prompt():
    msg = """\033[1;32m### 你好，%s 欢迎登录跳板机系统！ ### \033[0m
    1) 输入 \033[32mIP/主机名 \033[0m 登录服务器。
    2) 输入 \033[32mP/p\033[0m 查看你允许登陆的服务器列表。
    2）输入 \033[32mC/c\033[0m 查看收藏夹。
    3) 输入 \033[32mQ/q\033[0m  退出。
    """%(LOGIN_NAME)
    print textwrap.dedent(msg)


class ServerError(Exception):
    pass


def get_user_host(username):
    uid = sqlhelper.executeCmd("select id from user where name = '%s'"%(username))
    if not uid:
        return None
    else:
        ips = sqlhelper.executeCmd('select host_id from user_host where uid = %d and status = 1'%(uid[0]),True)
        if not ips:
            return None
        else:
            return ips

def get_user_collects(username):
    # check_collect_table()
    uid = sqlhelper.executeCmd("select id from user where name = '%s'"%(username))
    if not uid:
        return None
    else:
        ips = sqlhelper.executeCmd('select host_id,remarks from qsh_collect where uid = %d order by id asc'%(uid[0]),True)
        if not ips:
            return None
        else:
            i=0
            global COLLECTS
            COLLECTS = []
            for ip in ips:
                host_name = sqlhelper.executeCmd("select hostname,primary_ip_id from host where id = '%d' and deleted = 0"%(ip[0]))
                if host_name:
                    try:
                        host_ip = sqlhelper.executeCmd("select ipv4 from ip_address where id = '%s'"%(host_name[1]))
                        if not host_ip[0]:
                            host_ip[0] = 'null'
                        i+=1
                        collect = [i,host_name[0],host_ip[0],ip[1]]
                        COLLECTS.append(collect)
                    except e:
                        continue
                else:
                    continue

def print_user_host(username):
    try:
        ips = get_user_host(username)
    except ServerError, e:
        color_print(e, 'red')
        return
    if not ips:
        color_print('You do not have the host!', 'red')
    else:
        for ip in ips:
            host_name = sqlhelper.executeCmd("select hostname,primary_ip_id from host where id = '%d' and deleted = 0"%(ip[0]))
            if host_name:
                host_ip = sqlhelper.executeCmd("select ipv4 from ip_address where id = '%s'"%(host_name[1]))
            else:
                color_print('Can\'t find the host id: %s!'%(ip[0]), 'red')
                continue
            if not host_ip[0]:
                host_ip[0] = 'null'
            print '%-15s -- %s' % (host_name[0], host_ip[0])
        print ''

def check_collect_table():
    sql_table = """CREATE TABLE IF NOT EXISTS  `qsh_collect` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `uid` int(11) NOT NULL,
  `host_id` int(11) NOT NULL,
  `remarks` varchar(20) DEFAULT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;"""
    try:
        sqlhelper.executeCmd(sql_table)
        return True
    except e:
        return False

def print_user_collect(username):
    global  COLLECTS
    try:
        get_user_collects(username)
    except :
        pass
    if not COLLECTS:
        color_print("您的收藏列表为空，请使用 'C add 主机 备注' 的格式添加！ 例：C add 1.1.1.1 我的测试机",'red')
    else:
        color_print("请使用 'C %d' 或 'C %s' 或 'C %s' 的格式直接登录！"%(COLLECTS[0][0],COLLECTS[0][1],COLLECTS[0][2]),'red')
        for colllect in COLLECTS:

            print '%d. %s\t%s\t%s' % (colllect[0],colllect[1],colllect[2],colllect[3])
            print ''

def user_add_collect(username,part_ip,remarks):
    host_id = get_host_id(part_ip)
    if not host_id:
        color_print("没有找到该主机：%s ，请检查输入内容！"%part_ip,'red')
    else:
        uid = get_user_id(username)
        try:
            sqlhelper.executeCmd("insert into qsh_collect(uid,host_id,remarks) values (%d,%d,\'%s\');"%(uid[0],host_id[0],remarks),True)
        # sqlhelper.executeCmd(r"insert into qsh_collect(uid,host_id,remarks) values (3,3,\'sddf\')",True)
            color_print("添加收藏成功！",'red')
        except:
            color_print("添加收藏失败！",'red')


def get_host_id(part_ip):
    if ip_pattern.match(part_ip):
        ip_id = sqlhelper.executeCmd("select id from ip_address where ipv4 = '%s'"%(part_ip))
        if not ip_id:
            return False
        else:
            host_id = sqlhelper.executeCmd("select id from host where primary_ip_id = '%d' and deleted = 0"%(ip_id[0]))
    elif hostname_pattern.match(part_ip):
        host_id = sqlhelper.executeCmd("select id from host where hostname = '%s' and deleted = 0"%(part_ip))
    else:
        return False
    return host_id

def get_user_id(username):
    uid = sqlhelper.executeCmd("select id from user where name = '%s'"%(username))
    if not uid:
        return None
    else:
        return uid

print_prompt()
collect_pattern = re.compile(r'^[Cc]\s.+$')
gid_pattern = re.compile(r'^[Gg]\s.+$')
Num_pattern = re.compile(r'^\d{1,3}$')
ip_pattern = re.compile(r'^(\d{1,2}|1\d\d|2[0-4]\d|25[0-5])\.(\d{1,2}|1\d\d|2[0-4]\d|25[0-5])\.(\d{1,2}|1\d\d|2[0-4]\d|25[0-5])\.(\d{1,2}|1\d\d|2[0-4]\d|25[0-5])$')
hostname_pattern = re.compile(r'^[A-Za-z]+\d{2}-\d{1,3}')

sqlhelper = Sql_helper()
sqlhelper.Connect(SQLALCHEMY_DATABASE_URI)
get_user_collects(LOGIN_NAME)

def onsignal_quit(a,b):
    return
signal.signal(signal.SIGQUIT,onsignal_quit)


while True:
    try:
        option = raw_input("\033[1;32m请选择或直接输入IP登录>:\033[0m ").strip()
    except (IOError,EOFError,KeyboardInterrupt),e:
        print e
        continue
    if option in ['C', 'c']:
        print_user_collect(LOGIN_NAME)
    elif collect_pattern.match(option):
        collect = option[1:].strip()
        command = collect.split()
        if command[0] == 'add':
            user_add_collect(LOGIN_NAME,command[1],command[2])
        elif Num_pattern.match(collect):
            for COL in COLLECTS:
                if COL[0] == int(collect):
                    verify_connect(LOGIN_NAME, COL[2])
        else:
            verify_connect(LOGIN_NAME, collect)
    elif option in ['P', 'p']:
        print_user_host(LOGIN_NAME)
    elif option in ['G', 'g']:
        print_user_hostgroup(LOGIN_NAME)
    elif gid_pattern.match(option):
        gid = option[1:].strip()
        # print_user_hostgroup_host(LOGIN_NAME, gid)
    elif option in ['E', 'e']:
        exec_cmd_servers(LOGIN_NAME)
    elif option in ['Q','q','exit']:
        sys.exit()
    else:
        verify_connect(LOGIN_NAME, option)

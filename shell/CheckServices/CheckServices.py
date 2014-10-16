#coding=utf-8
import xml.dom.minidom
import os
import MySQLdb
import time
import hashlib
from nmapparse import *

#open the xml
servicesfile = "services.xml"
os.system("nmap -T5 -n -sT -sV -p1-65535 --open -i "+"/tmp/useIP.txt"+" -oX "+servicesfile)
parser = Parser(servicesfile)
output = open('openservices.txt','w+')

db = MySQLdb.connect("IP","username","passwd","database" )
cursor = db.cursor()
pcinfo = ""
for h in parser.all_hosts():
    if h.status == "up":
        ip = h.get_address('ipv4')
        servicename = ""
        hostname = ""
        host = ""
        for port in h.get_ports( 'tcp','open' ):
            s = h.get_service( 'tcp',port )
            if s == None:
                service = ""
            else:
                service = s.name
                if service in ["ssh","mysql"]:
                    servicename = servicename+" "+service+":"+port

        if servicename != "" and ip != "0.0.0.0":
            cursor.execute('select host_name,host from sysadm_assets where outer_ip like "%'+ip+'%";')

            for row in cursor.fetchall():
                hostname = row[0]
                host = row[1]

            output.write("IP: "+host+" hostname: "+hostname+" ExternalIP: "+ip+" ServerName:"+servicename+",")

output.seek(0)
MSG = output.read()
Time = str(time.time())
m = hashlib.md5()
m.update('xxxxxxxxxxxxxxx'+Time)
passwd = m.hexdigest()
os.system('curl "http://x.x.com/alert/sendmail.php?rtx_user=sharlockqi@123u.com&msg=报告大王！发现危险的外网服务端口：'+ MSG +'请审核。&time='+Time+'&secret='+passwd+'&email_user=sharlockqi@123u.com"')
output.close()
db.close()

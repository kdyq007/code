#!/bin/sh
#****************************IP资产自动检测脚本**********************************
#* 分别从数据库中读出正在使用和未使用的IP，扫描并检测各项IP的变动，最后发送RTX和邮件警告！  *
#******************************作者：qiqi**************************************
#interface password
mailpass="XXXXXXXXXXXXX"

#select database
HOST=xx.xx.xx.xx
USER=root
PASS=xxxxxxxx

QUERYnouse=`mysql -h$HOST -u$USER -p$PASS << EOF
               use sysadm;
               select ip from sysadm_ip_assets where isuse=0;
               exit
EOF`

QUERYuse=`mysql -h$HOST -u$USER -p$PASS << EOF
               use sysadm;
               select ip from sysadm_ip_assets where isuse=1;
               exit
EOF`

# put IP and count in txt
USEIP="/tmp/useIP.txt"
NOUSEIP="/tmp/nouseIP.txt"

echo $QUERYuse | tr -s " " "\n" | grep -v ip > $USEIP
echo $QUERYnouse | tr -s " " "\n" | grep -v ip > $NOUSEIP

# ping the useIP,exclude(--excludefile excludeIP.txt)
MSG1=$(nmap -v -sP -iL $USEIP | grep down | grep -oE "[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}" | tr -s "\n" ",")

# send MSG1
if [[ -n "$MSG1" ]];then
time=$(date '+%s')
md5=$(echo -n "$mailpass$time"|md5sum|awk '{print $1}')
curl "http://sa.123u.com/alert/sendmail.php?rtx_user=sharlockqi@123u.com&msg=报告大王！$MSG1的IP发生异常不能ping通，请检查。&time=$time&secret=$md5&email_user=sharlockqi@123u.com"
fi

# ping the nouseIP,exclude(--excludefile excludeIP.txt)
MSG2=$(nmap -sP -iL $NOUSEIP | grep -oE "[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}" | tr -s "\n" ",")

# send MSG2
if [[ -n "$MSG2" ]];then
time=$(date '+%s')
md5=$(echo -n "$mailpass$time"|md5sum|awk '{print $1}')
curl "http://sa.123u.com/alert/sendmail.php?rtx_user=sharlockqi@123u.com&msg=报告大王！发现新增IP：$MSG2请审核。&time=$time&secret=$md5&email_user=sharlockqi@123u.com"
fi
rm -rf $USEIP
rm -rf $NOUSEIP

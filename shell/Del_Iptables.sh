#/bin/bash
cat /tmp/IP.txt |while read line
do
id=`iptables -L INPUT --line-numbers | grep DROP|awk -F' ' '{print $1" "$5" "$6}'|grep $line|awk -F' ' '{print $1}'`
iptables -D INPUT $id
if [ $? -eq 0 ]
then
    eval echo IP: $line del seccessful!
else
    eval echo IP: $line del failure!
fi
done
#!/bin/bash
#Eash user add by qiqi!
for((i=1;i<=$#;i++))
do
useradd -s /usr/local/bin/eash $(eval echo '$'$i)
if [ $? -eq 0 ]
then
        eval echo user '$'$i add successful!
else
        eval echo user '$'$i add failure!
fi
done

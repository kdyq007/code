#!/bin/bash
for((i=1;i<=$#;i++))
do
useradd -s /usr/local/bin/eash $(eval echo '$'$i)
eval echo '$'$i user add successful!
done

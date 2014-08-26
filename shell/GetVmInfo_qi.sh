#!/bin/bash
#****************************服务器信息获取脚本**********************************
#* 获取服务器部分信息,并发送到网站php接口，php接收到post包保存进数据库，自动补全资产信息！ *
#******************************作者：qiqi**************************************
export LANG=C

# OS Information
OS=`cat /etc/issue | head -1`
# Network Information
net=`ifconfig -a| grep 'inet addr'|grep -vE '127.0.0.1|10.128|172.17' |awk '{print $2}' |tr -d "addr:"|xargs`
# CPU Information
cputype=`cat /proc/cpuinfo | grep "model name"|head -1|awk -F ':' '{print $2}'`
cpunum=`cat /proc/cpuinfo | grep "physical id"|sort -u|wc -l`
if [ $cpunum -eq 0 ];
then
        cpunum=1
fi
cpucore=`cat /proc/cpuinfo | grep processor|wc -l`
# dmidecode Information
Mem_Size=$(free -m | awk '/Mem/{printf $2}')MB
data=`/bin/hostname`,$net,$OS,$cputype,$cpunum,$cpucore,${Mem_Size}
echo $data

#send the serverinfo data
curl --data-urlencode "data=$data" http://xx.xx.xx.xx/auto_assets




#下面是部分drupal框架写的php接口，将数据存进数据库，未做验证！
#
#function auto_assets_interface() {
#	if(isset($_POST['data'])) {
#            $info=explode(',',$_POST['data']);
#
#           $pos = strpos($info[1],' ');
#            if($pos>0)
#            {
#            $host = substr($info[1],0,$pos);
#            $outer_ip = substr($info[1],$pos+1);
#            }
#            else
#            {
#                $host = $info[1];
#                $outer_ip="";
#            }
#            $de_value=array('host' => $host,'host_name' => $info[0],'system' => $info[2],'type' => '2','outer_ip' => $outer_ip,'machine_room'=>'10','cpu' => $info[3],'cpu_num' => $info[4],'cpu_core' => $info[5],'memory' => $info[6]);
#            db_set_active('sysadm');
#            $isexist = db_query("SELECT hostid FROM sysadm_assets WHERE host = :ip", array(":ip" => $host))->fetchField();
#            if(empty($isexist)){
#            db_insert('sysadm_assets')
#		->fields($de_value)
#		->execute();
#        }
#            db_set_active();
#        }
#        exit;
#}
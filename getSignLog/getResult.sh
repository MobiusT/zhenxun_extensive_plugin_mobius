#加载环境变量
source $HOME/.bash_profile
#日志输出位置（需要真寻可访问）
logPath=$HOME/zhenxun-bot/zhenxun/zhenxun_extensive_plugin_mobius/getSignLog/log/sign.log
flag=`ls $logPath |wc -l`
nowdate=`date +%Y%m%d`;
#检查备份
echo $flag
if [ $flag -gt 0 ] ; then
	cp $logPath $logPath.$nowdate
fi
#获取日志，当前仅获取末尾33行
cd $HOME/genshinhelper
docker-compose logs  --tail=33 > $logPath

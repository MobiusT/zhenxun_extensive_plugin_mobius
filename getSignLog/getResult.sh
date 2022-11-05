source $HOME/.bash_profile
logPath=$HOME/zhenxun-bot/zhenxun/zhenxun_extensive_plugin_mobius/getSignLog/log/sign.log
flag=`ls $logPath |wc -l`
nowdate=`date +%Y%m%d`;
echo $flag
if [ $flag -gt 0 ] ; then
	cp $logPath $logPath.$nowdate
fi
cd $HOME/genshinhelper
docker-compose logs  --tail=33 > $logPath

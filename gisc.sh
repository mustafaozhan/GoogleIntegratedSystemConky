#!/bin/bash
#
# Run this script to start or stop gisc



#
# start gisc
#
start_cp()
{
	echo 'starting'
	folderPath=$(dirname $0)
	cd "$folderPath"
	conky -b -c conkyrc
	conky -d -c conkyKeepRc &
}

#
# stop gisc
#
stop_cp()
{
	echo 'stopping'
	PID=$(ps -C conky a | grep 'gisc' | grep '\-d' | awk {'print $1'})
	if [ -z "$PID" ]
	then
		echo "No running gisc instances found"
	else	
		kill -9 $PID
	fi
}

#
# print the manual
#
echo_manual()
{
	echo '--- Usage ---'
	echo 'Starting gisc: ./gisc.sh start'
	echo 'Stopping gisc: ./gisc.sh stop'
	echo 'Restarting gisc: ./gisc.sh restart'
}

if [ $1 ]; then
	if [ $1 = "start" ]; then
		start_cp
	elif [ $1 = "stop" ]; then
		stop_cp
	elif [ $1 = "restart" ]; then
		echo 'restarting'
		stop_cp
		start_cp
	else
		echo_manual
	fi
else
	echo_manual
fi

exit 0

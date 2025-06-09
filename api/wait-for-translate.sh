#!/bin/sh
host="$1"
port="$2"
shift 2
cmd="$@"

while ! curl -s http://$host:$port/languages > /dev/null; do
  echo "Waiting for translate at $host:$port"
  sleep 10
done

echo "Translate is up - executing command"
exec $cmd
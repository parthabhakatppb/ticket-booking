#!/usr/bin/env sh
set -e

if [ "$#" -lt 2 ]; then
  echo "Usage: wait-for-it.sh host:port -- command"
  exit 1
fi

HOSTPORT="$1"
shift

if [ "$1" = "--" ]; then
  shift
fi

HOST=$(echo "$HOSTPORT" | cut -d: -f1)
PORT=$(echo "$HOSTPORT" | cut -d: -f2)
TIMEOUT="${WAITFORIT_TIMEOUT:-30}"

python - <<PY
import socket
import time
import sys

host = "${HOST}"
port = int("${PORT}")
timeout = int("${TIMEOUT}")
start = time.time()

while True:
    try:
        with socket.create_connection((host, port), 2):
            break
    except OSError:
        if time.time() - start > timeout:
            print("Timed out waiting for {}:{}".format(host, port))
            sys.exit(1)
        time.sleep(1)
PY

exec "$@"

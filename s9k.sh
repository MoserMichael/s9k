#!/bin/bash -e

function Help {
cat <<EOF


$0  [-i <host>] [-p <port>] [-c <cmd>] [-v -h]

run s9k.py python script with tls, creates a self signed certificate if needed.

-i  <host>  - listening host (default $HOST)
-p  <port>  - listening port (default $PORT)
-c  <cmd>   - (optional) kubectl command. (default kubectl)
-v          - verbose output

EOF

exit 1
}

PORT="8000"
HOST="localhost"
CMD=""

while getopts "vhi:p:c:" opt; do
  case ${opt} in
    h)
	Help
        ;;
    p)
        PORT="$OPTARG"
        ;;
    i)
        HOST="$OPTARG"
        ;;
    c)
        CMD="-c $OPTARG"
        ;;
    v)
        set -x
        export PS4='+(${BASH_SOURCE}:${LINENO})'
        VERBOSE=1
        ;; 
    *)
        Help "Invalid option"
        ;;
   esac
done

if [[ "$HOST" == "" ]] || [[ "$PORT" == "" ]]; then
    echo "-p or -i options missing"
    Help
fi

CERT="cacert-${HOST}.pem"
KEY="privkey-${HOST}.pem"

if [[ ! -f $CERT ]] || [[ ! -f $KEY ]]; then
    openssl req -new -x509 -days 256 -nodes -newkey rsa:4096 -out $CERT -keyout $KEY  -subj '/CN='"${HOST}"'O='"${HOST}"'/C=US'
fi

./s9k.py -i $HOST -p $PORT -r $CERT -k $KEY $CMD

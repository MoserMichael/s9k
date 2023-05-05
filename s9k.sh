#!/usr/bin/env bash

set -e

function Help {
cat <<EOF


$0  [-i <host>] [-p <port>] [-c <cmd>] [-v -h]

run s9k.py python script with tls, creates a self signed certificate if needed.

-i  <host>  - listening host (default $HOST)
-p  <port>  - listening port (default $PORT)
-c  <cmd>   - (optional) kubectl command. (default kubectl)
-x  <ctx>   - (optional) kubectl context to use
-v          - verbose output
-d          - internal option to run in docker (listen on eth0, and take kubeconfig from mounted path)
-s          - use self signed sertificates
EOF

exit 1
}

PORT="8000"
HOST="localhost"
CMD=""

if [[ "x${SSL}" != "x" ]]; then
    SSL="on"
else
    SSL="off"
fi

while getopts "vhdi:p:c:x:" opt; do
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
    d)
        # run as docker entrypoint
        HOST="$DHOST"
        PORT="$DPORT"
        MOUNT_OPT="--kubeconfig=/kube-mount"
        if [[ $CONTEXT != "" ]]; then
            MOUNT_OPT="$MOUNT_OPT -x $CONTEXT"
        fi    
        ;;
    c)
        CMD="${CMD} -c $OPTARG"
        ;;
    x)
        CMD="${CMD} -x $OPTARG"
        ;;
    v)
        set -x
        export PS4='+(${BASH_SOURCE}:${LINENO}) '
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


SCRIPT_DIR=$(dirname "$0")

if [[ "$SSL" == "on" ]]; then 
    CERT="cacert-${HOST}.pem"
    KEY="privkey-${HOST}.pem"

    if [[ ! -f $CERT ]] || [[ ! -f $KEY ]]; then
        openssl req -new -x509 -days 256 -nodes -newkey rsa:4096 -out $CERT -keyout $KEY  -subj '/CN='"${HOST}"'/O='"${HOST}"'/C=US/OU=s9k'
    fi

    ${SCRIPT_DIR}/s9k.py -i $HOST -p $PORT -r $CERT -k $KEY $CMD $MOUNT_OPT 
else
    ${SCRIPT_DIR}/s9k.py -i $HOST -p $PORT $CMD $MOUNT_OPT 
fi

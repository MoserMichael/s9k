#!/bin/sh 

PORT="8000"
HOST=127.0.0.1
KUBE_DIR="$HOME/.kube"
IMAGE_LOCATION="quay.io/mmoser/s9k-mm"

Help() {
cat <<EOF

Start s9k in docker

$0 -r [-p <port>] [-i <host>] [-d <dir>] [-v] [-c <image>]

Stop s9k in docker

Run s9k web server in a docker; by default the docker image is fetched from a public repository. ($IMAGE_LOCATION)
The web server creates a self-signed certificate on each docker run

Start the web server fir s9k

-r          - start the web server
-p  <port>  - listening port (default ${PORT})
-i  <host>  - listening host (default ${HOST})
-d  <dir>   - directory where kube config is (default ${KUBE_DIR})

Stop the web server for s9k

-s          - stop the web server

Common options:

-c  <image> - override the container image location (default ${IMAGE_LOCATION})
-v          - run verbosely

EOF

exit 1
}

while getopts "hrsvi:p:c:" opt; do
  case ${opt} in
    h)
        Help
        ;;
    r)
        ACTION="start"
        ;;
    s)
        ACTION="stop"
        ;;
    p)
        PORT="$OPTARG"
        ;;
    i)
        HOST="$OPTARG"
        ;;
    c)
        IMAGE_LOCATION="$OPTARG"
        ;;
    d)
        KUBE_DIR="$OPTARG"
        ;;
    v)
        set -x
        export PS4='+(${BASH_SOURCE}:${LINENO}) '
        ;; 
    *)
        Help "Invalid option"
        ;;
   esac
done

if [[ $ACTION == 'start' ]]; then
    docker run --network=host -v $KUBE_DIR:/kube-mount -e DHOST=$HOST -e DPORT=$PORT -dt ${IMAGE_LOCATION} 
    echo "Listen on https://${HOST}:${PORT}"
else 
  if [[ $ACTION == 'stop' ]]; then
    DOCKER_ID=$(docker ps | grep ${IMAGE_LOCATION}[[:space:]] | awk '{ print $1 }')
    docker stop $DOCKER_ID
    docker rm $DOCKER_ID
  else
    Help 'must use either to start the server -r or to stop it -s'
  fi
fi


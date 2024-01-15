#!/bin/bash

PORT="8000"
HOST=0.0.0.0
CONTEXT=""
KUBE_DIR="$HOME/.kube"
IMAGE_LOCATION=ghcr.io/mosermichael/s9k-mm:latest

Help() {
cat <<EOF

Start s9k in docker

$0 -r [-p <port>] [-i <host>] [-d <dir>] [-v] [-c <image>]

Stop s9k in docker

Run s9k web server in a docker; by default the docker image is fetched from a public repository. ($IMAGE_LOCATION)
The web server creates a self-signed certificate on each docker run

Start the web server for s9k

-r          - start the web server
-p  <port>  - listening port (default ${PORT})
-i  <host>  - listening host (default ${HOST})
-d  <dir>   - directory where kube config is (default ${KUBE_DIR})
-t          - enable TLS/SSL (self signed cert)
-x          - set kubeconfig context to use (use default context if empty)

Stop the web server for s9k

-s          - stop the web server

Common options:

-c  <image> - override the container image location (default ${IMAGE_LOCATION})
-v          - run verbosely

EOF

exit 1
}

function assert_bins_in_path {
  if [[ -n $ZSH_VERSION ]]; then
    builtin whence -p "$1" &> /dev/null
  else  # bash:
    builtin type -P "$1" &> /dev/null
  fi
  if [[ $? != 0 ]]; then
    echo "Error: $1 is not in the current path"
    exit 1
  fi
  if [[ $# -gt 1 ]]; then
    shift  # We've just checked the first one
    assert_bins_in_path "$@"
  fi
}


check_docker_engine_running() {
    assert_bins_in_path "docker"
    docker ps >/dev/null 2>&1
    if [[ $? != 0 ]]; then
        echo "Error: docker engine not running"
        exit 1
    fi
}

clean_if_stopped() {
    STATE=$(docker ps -a --filter 'label=s9k-admin-console'  --format='{{.State}}')
    if [[ $STATE == "running" ]]; then
        echo "server is already running"
        exit 1
    fi
    if [[ $STATE != "" ]]; then
        # force stop and clean up
        ID=$(docker ps -a --filter 'label=s9k-admin-console'  --format='{{.ID}}')
        if [[ $ID != "" ]]; then
            docker kill "$ID"
            docker container prune -f --filter 'label=docker-php-admin'
        fi
    fi
}


SSL="off"

while getopts "htrsvi:p:c:x:" opt; do
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
    x)
        CONTEXT="$OPTARG"
        ;;
    i)
        HOST="$OPTARG"
        ;;
    c)
        IMAGE_LOCATION="$OPTARG"
        ;;
    t)
        SSL="on"
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
       
    check_docker_engine_running
    clean_if_stopped

    if [[ "${SSL}" == "on" ]]; then
        docker run --rm --name s9k-net -p ${HOST}:${PORT}:${PORT} -v $KUBE_DIR:/kube-mount -e DHOST=$HOST -e DPORT=$PORT -e SSL=on -e CONTEXT=$CONTEXT -l s9k-admin-console -dt ${IMAGE_LOCATION} 
        PROTO="https"

        echo ""
        echo "Note: Runs with self signed certificate"
        echo ""
    else
        docker run --rm --name s9k-net -p $PORT:$PORT -v $KUBE_DIR:/kube-mount -e DHOST=$HOST -e DPORT=$PORT -e CONTEXT=$CONTEXT -l s9k-admin-console -dt ${IMAGE_LOCATION} 
        PROTO="http"
    fi
    echo "Listen on $PROTO://${HOST}:${PORT}"
else 
  if [[ $ACTION == 'stop' ]]; then
    DOCKER_ID=$(docker ps | grep ${IMAGE_LOCATION}[[:space:]] | awk '{ print $1 }')
    if [[ ${DOCKER_ID} == "" ]]; then
        echo "Docker is already stopped"
        exit 1
    fi
    echo "stopping docker container: $DOCKER_ID ..."
    docker stop $DOCKER_ID
  else
    Help 'must use either to start the server -r or to stop it -s'
  fi
fi




## Web based UI with similar functionality as k9s

[k9s](https://github.com/derailed/k9s) is a character UI application for managing kubernetes clusters.

This script [s9k] is a simple web server that serves a HTML application designed to manage kubernetes clusters.
You can view and modify all kubernetes api resources and attach a terminal to a container running in a pod.

It works by parsing the output of kubectl. The functionality of this application is similar in functionality to the k9s application. 

Here is a link to a presentation: [gif animation](https://github.com/MoserMichael/s9k/releases/download/presentation/peek-2.gif) 

### Running the script from docker image

The following command runs the server in a docker environment; the public docker image is quay.io/mmoser/s9k-mm 

./run-in-docker.sh -r

You can now access the web application by following url https://127.0.0.1:8000 (a self-signed certificate is created on each run)

Stop the web server with the following command:

./run-in-docker.sh -s

Additional options to run the script:

```
./run-in-docker.sh  -h

Start s9k in docker

./run-in-docker.sh -r [-p <port>] [-i <host>] [-d <dir>] [-v] [-c <image>]

Stop s9k in docker

Run s9k web server in a docker; by default the docker image is fetched from a public repository. (quay.io/mmoser/s9k-mm)
The web server creates a self-signed certificate on each docker run

Start the web server fir s9k

-r          - start the web server
-p  <port>  - listening port (default 8000)
-i  <host>  - listening host (default 127.0.0.1)
-d  <dir>   - directory where kube config is (default /home/mmoser/.kube)

Stop the web server for s9k

-s          - stop the web server

Common options:

-c  <image> - override the container image location (default quay.io/mmoser/s9k-mm)
-v          - run verbosely
```

### Running locally / Installing the requirements

Need to have python3 on the system.

Install dependent packages:

```
sudo pip3 install bottle

sudo pip3 install bottle-websocket
```

run make in project directory to build a go based executable required to attach a terminal to a container in a pod.

### Running the script locally

./s9k.py runs the server; by default you can then connect to http://localhost:8000

You can customize it with the following command line options
```
usage: s9k.py [-h] [--command KUBECTL] [--port PORT] [--host HOST]
              [--cert CERT] [--key KEY]

Web application that parses kubectl output in a nice manner.

optional arguments:
  -h, --help            show this help message and exit
  --command KUBECTL, -c KUBECTL
                        kubectl command name
  --port PORT, -p PORT  listening port
  --host HOST, -i HOST  listening on host
  --cert CERT, -r CERT  TLS certifificate file
  --key KEY, -k KEY     TLS private key file

```

./s9k.sh runs the server, it also creates a self signed certificate for the server, connect to https://localhost:8000 (you get a browser warning on self signed certificates)

You can customize it with the following command line options

```
./s9k.sh  [-i <host>] [-p <port>] [-c <cmd>] [-v -h]

run s9k.py python script with tls, creates a self signed certificate if needed.

-i  <host>  - listening host (default localhost)
-p  <port>  - listening port (default 8000)
-c  <cmd>   - (optional) kubectl command. (default kubectl)
-v          - verbose output
-d          - internal option to run in docker (listen on eth0, and take kubeconfig from mounted path)
```

## Acknowledgements

Adapted the [websocket terminal](https://github.com/sorgloomer/websocket_terminal) project by [sorgloomer](https://github.com/sorgloomer) for this project.

Thanks to the python [bottle framework](https://bottlepy.org/docs/dev/) and [bottle-websocket](https://pypi.org/project/bottle-websocket/) package.

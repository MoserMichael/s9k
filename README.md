

## Web based UI for managing kubernetes clusters

This is a simple web server that serves a web application designed to manage kubernetes clusters.
You can view and modify all kubernetes api resources and attach a terminal to a container running in a pod.

It works by parsing the output of kubectl.
Here is a link to a short presentation: [gif animation](https://github.com/MoserMichael/s9k/releases/download/presentation/peek-2.gif) 

This application is similar in functionality to [k9s](https://github.com/derailed/k9s), that is a character UI application for managing kubernetes clusters.


Also please see [my comparison](https://github.com/MoserMichael/s9k/blob/master/compare-tui-webui.md) of the various management applications.

### Running the script from docker image

The following script in this repository runs the server in a docker environment; the public docker image is quay.io/mmoser/s9k-mm 

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

Start the web server for s9k

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

Thanks to [Fernand Galiana](https://github.com/derailed), the author of [k9s](https://github.com/derailed/k9s)  

Adapted the [websocket terminal](https://github.com/sorgloomer/websocket_terminal) project by [sorgloomer](https://github.com/sorgloomer) for this project.

Thanks to the python [bottle framework](https://bottlepy.org/docs/dev/) and [bottle-websocket](https://pypi.org/project/bottle-websocket/) package.


## what I learned while writing this project

I started as a simple web application in python; a web search suggested to use the bottle framework for that, so go for it. Later I wanted to add the ability of hosting a terminal session to a pod in the browser (wrap kubectl exec for this application); that's where the challenge started: First I had to use xterm in the browser, and xterm is talking to the server via web sockets; the server now has to forward data read via websockets to a go based executable (and reverse direction also) that is connecting to the terminal via client-go (regular kubectl exec was not enough here). Now support for websockets with bottle is not trivial; bottle uses wsgi for the web server, now every server that does wsgi has a slightly different idea of how this standard looks like. I didn't manage to add websocket support for cherrypy, now luckily there is the alternative to gevent based geventwebsocket; gevent uses a co-thread based library for python, so i had to become familiar with greenlets, my select loop of handling the web socket made the whole application get stuck while handling the web socket, that was fixed by using gevent based select and popen primitives that play well with greenlets; now all this stuff made building of the docker image quite complicated - pip install now needs to build the whole gevent based goodness as native code;

The lesson of this story is that most open source frameworks are simple and pleasant to use while you stick to the common use cases, when you need to go slightly off the beaten track then things tend to get complicated...

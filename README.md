

# Web based UI for managing kubernetes clusters

This is a simple web server that serves a web application designed to manage kubernetes clusters.
You can view and modify all kubernetes api resources and attach a terminal to a container running in a pod.

It works by parsing the output of kubectl. (click on picture for a presentation)

  
[![click to view presentation](https://img.youtube.com/vi/yjSStb9JZ7g/0.jpg)](https://www.youtube.com/watch?v=yjSStb9JZ7g)
  

This application is similar in functionality to [k9s](https://github.com/derailed/k9s), that is a character UI application for managing kubernetes clusters.

### Running the server locally

```
 ./s9k.sh -h

./s9k.sh  [-i <host>] [-p <port>] [-c <cmd>] [-v -h]

run s9k.py python script with tls, creates a self signed certificate if needed.

-i  <host>  - listening host (default localhost)
-p  <port>  - listening port (default 8000)
-c  <cmd>   - (optional) kubectl command. (default kubectl)
-x  <ctx>   - (optional) kubectl context to use
-v          - verbose output
-d          - internal option to run in docker (listen on eth0, and take kubeconfig from mounted path)
-s          - use self signed sertificates
```

### Running the server in a docker container

use ```./run-in-docker.sh``` o run he server in a docker container.

!!!LIMITATION FOR DOCKER!!! you cant use a kubectl context where the server is running on localhost - the same machine. You don't have this problem when running locally

```
./run-in-docker.sh -h

Start s9k in docker

./run-in-docker.sh -r [-p <port>] [-i <host>] [-d <dir>] [-v] [-c <image>]

Stop s9k in docker

Run s9k web server in a docker; by default the docker image is fetched from a public repository. (ghcr.io/mosermichael/s9k-mm:latest)
The web server creates a self-signed certificate on each docker run

Start the web server for s9k

-r          - start the web server
-p  <port>  - listening port (default 8000)
-i  <host>  - listening host (default 0.0.0.0)
-d  <dir>   - directory where kube config is (default /home/user/.kube)
-t          - enable TLS/SSL (self signed cert)
-x          - set kubectl context to use (use default context if empty)

Stop the web server for s9k

-s          - stop the web server

Common options:

-c  <image> - override the container image location (default ghcr.io/mosermichael/s9k-mm:latest)
-v          - run verbosely
```



## Acknowledgements

Thanks to [Fernand Galiana](https://github.com/derailed), the author of [k9s](https://github.com/derailed/k9s)  

Adapted the [websocket terminal](https://github.com/sorgloomer/websocket_terminal) project by [sorgloomer](https://github.com/sorgloomer) for this project.

Thanks to the python [bottle framework](https://bottlepy.org/docs/dev/) and [bottle-websocket](https://pypi.org/project/bottle-websocket/) package.


## what I learned while writing this project

I started as a simple web application in python; a web search suggested to use the bottle framework for that, so go for it. Later I wanted to add the ability of hosting a terminal session to a pod in the browser (wrap kubectl exec for this application); that's where the challenge started: First I had to use xterm in the browser, and xterm is talking to the server via web sockets; the server now has to forward data read via websockets to a go based executable (and reverse direction also) that is connecting to the terminal via client-go (regular kubectl exec was not enough here). Now support for websockets with bottle is not trivial; bottle uses wsgi for the web server, now every server that does wsgi has a slightly different idea of how this standard looks like. I didn't manage to add websocket support for cherrypy, now luckily there is the alternative to gevent based geventwebsocket; gevent uses a co-thread based library for python, so i had to become familiar with greenlets, my select loop of handling the web socket made the whole application get stuck while handling the web socket, that was fixed by using gevent based select and popen primitives that play well with greenlets; now all this stuff made building of the docker image quite complicated - pip install now needs to build the whole gevent based goodness as native code;

The lesson of this story is that most open source frameworks are simple and pleasant to use while you stick to the common use cases, when you need to go slightly off the beaten track then things tend to get complicated.

in the end any technology (at any level) can be an interesting problem.

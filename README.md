

## Web based UI with similar functionality as k9s

[k9s](https://github.com/derailed/k9s) is a character UI application for managing kubernetes clusters.

This script is a simple web server that serves a webapp with similar functionality as k9s. It works by parsing the output of kubectl.
This application is written in python3 and requires the [bottle library](https://bottlepy.org/docs/dev/), It also requires the presence of kubectl.


```
sudo pip3 install bottle
```

by default it listens on localhost on port 8000


You can customize it with the following command line options
```
usage: s9k.py [-h] [--command KUBECTL] [--port PORT] [--host HOST]

Web application that parses kubectl output in a nice manner.

optional arguments:
  -h, --help            show this help message and exit
  --command KUBECTL, -c KUBECTL
                        kubectl command name
  --port PORT, -p PORT  listening port
  --host HOST, -i HOST  Input file name
```


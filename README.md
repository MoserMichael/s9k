

## webapp with similar functionality as k9s

[k9s](https://github.com/derailed/k9s) is a character UI application for managing of kubernetes clusters.

This one is a simple webapp with similar functionality. It parses the output of kubectl and presents it as a web interface.
This application is written in python3.

Requires [bottle](https://bottlepy.org/docs/dev/), requires the presence of kubectl.


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


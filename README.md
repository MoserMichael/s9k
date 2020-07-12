

## webapp with similar functionality as k9s

Requires [bottle](https://bottlepy.org/docs/dev/), requires the presence of kubectl or oc.


```
pip install bottle
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


# the CLI vs TUI vs WebUI shootout

## The big problem

Once upon a time we had the [UNIX philosophy](https://en.wikipedia.org/wiki/Unix_philosophy) of "Make each program do one thing well" etc. 
Nowadays we have gargantuan CLI programs with many functions, such as 

- kubectl
- docker
- gcloud
- aws cli

I think that the advantage of the former principle is that the user is left the freedom and means to form his own sentences out of words.
The program that does 'one thing well' is a word, while the shell or small languages like the shell or awk provide the syntax for gluing it together.

Now with the big CLI approach one is left to google for exact incantations...

One may be better off with a GUI, instead of dealing with these big CLI systems. (However a GUI can be messy as well, no doubt about that!)

(Maybe the Unix Philosophy was a kind of unreachable ideal: for example the GNU CLI is also adding lots of features to many core utilities, and that would also not be in line with the UNIX Philosophy, as is. I am not sure about that.)

## Intro 

This article compares the UI experience of three applications that cover the same domain:

1. [k9s](https://github.com/derailed/k9s) - written as a [Text based UI](https://en.wikipedia.org/wiki/Text-based_user_interface);
2.  [s9k](https://github.com/MoserMichael/s9k) - written by yours truly as as a [Web Application](https://en.wikipedia.org/wiki/Web_application) 
3. The [kubectl](https://kubernetes.io/docs/reference/kubectl/overview/) command line application that comes with every kubrnetes installation

Both application cover the same domain: they are designed to manage a kubernetes cluster, For k9s and s9j the main screen displays a list of all kubernetes api object types (this list is returned by command `kubectl api-resources` [described here](https://kubernetes.io/docs/reference/generated/kubectl/kubectl-commands#api-resources) ; upon choosing a resource you can inspect each of the object instances for a particular type, view the object description, view or change the definition of the object; view the logs for an object; For [Pod](https://kubernetes.io/docs/concepts/workloads/pods/) object you can also attach a terminal to a container running inside of the pod. Both k9s and s9k are GUI wrappers around kubectl.

This comparison is a bit subjective as it covers just one application and the experience of one user (that is my own one). Nevertheless i hope to come up with some useful observations.

## User productivity

kubernetes objects tend to be interconnected: the pods are often created by deployment objects; there are also many attached objects like services or ingresses that are connected to the same pods via some shared annotations, as well as other pods that share the same namespace, etc. When a problem occurs it makes sense to examine a set of related objects.

It appears that with k9s and s9k it is easier for me to make these connections; it may be that visual mode of thinking is involved when connecting the dots. With kubectl it takes longer to piece together all the command line arguments, and it is harder for me to maintain a global picture of the interconnections between api objects.

Also about keeping things in context: The web UI s9k  I can open several tabs in the browser, each one looking at a different object; with the k9s application I can do the same by opening several tabs in the terminal; however things are slightly more awkward here - I need to wait for a second until the application starts and have to navigate again.


## UI response times

k9s and kubectl as console applications are the winnders here; noticeably faster than the web ui s9k

The web application s9k is slower, sometimes noticeably slower; one particular problem is with the screen that retrieves the logs for an entity - it's ok if you want the log to a relatively short-lived pod, but it's a bit ugly when you need the logs of a long running entity like etcd. 

An interesting comparison of how response times changed over the last thirty years [link](https://danluu.com/input-lag/); response time seem to get worse as the UI gets more complicated.

## Ease of learning

### kubectl

kubectl has a largely consistent user interface; however some inconsistencies remain

to get the properties of a pod:

`kubectl get pod -n kube-system  kube-proxy-lq998`

but to get the logs of the pod 

`kubectl log pod/kube-proxy-lq998 -n kube-system` 

still to get a shell to the container in a pod it's 

`kubectl exec --stdin --tty -n kube-system kube-proxy-lq998 -- /bin/sh`

kubectl bash completion helps, but it is by itself also a bit incomplete ;-)

### k9s

The TUI is quite intuitive; you have a summary of shortcuts for the current screen on the top of the screen;
At every point you can get the full list of shortcuts by typing the question mark character; 

### s9k

I think the Web UI is the easiest to learn, due to the fact that web applications are so common these days (but i may be wrong here as I was the author of this application)

Also there are many common conventions in html pages that are useful, like clicking on table headers to sort the table rows, or Ctrl+F brings up a box for searching in a page. With TUI one would have to make a set of short cuts for these, and all these shortcuts are different, as there is little consistency here between applications.


## Conclusions

I have come to understand that all these ui comparisons are crap; use whatever interface that suits your style of working and your style of thinking; People are different and there is no one size fits them all solution;
In the end these are tools that are supposed to help you, and not the other way round.


all: kubeexec

build: kubeexec

kubeexec: exec.go
		GO111MODULE=on go build -o kubeexec github.com/MoserMichael/s9k

kubexec-no-mod: exec.go
		GO111MODULE=off go build -o kubeexec github.com/MoserMichael/s9k
 

init:
		go mod init github.com/mosermichael/s9k
		go mod tidy
		go mod vendor

clean:
		rm -f kubeexec || true

container-build:
		docker build -f Dockerfile -t ghcr.io/mosermichael/s9k-mm:latest . 2>&1 | tee container-build.log

container-push:
		./container-push.sh ghcr.io/mosermichael/s9k-mm latest

.PHONY: all kubexec-no-mod build init clean container-build container-push

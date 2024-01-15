
all: kubeexec

build: kubeexec

kubeexec: exec.go
		GO111MODULE=on go build -o kubeexec github.com/MoserMichael/s9k

kubexec-no-mod: exec.go
		GO111MODULE=off go build -o kubeexec github.com/MoserMichael/s9k
 
initpython:
		echo "*** creating virtual environment s9kenv ***"
		python3 -m venv s9kenv
		bash -c 'source s9kenv/bin/activate; pip3 install bottle bottle bottle-websocket'
		echo "*** activate virtual environment with command: source s9kenv/bin/activate ***"

init:
		go mod init github.com/mosermichael/s9k
		go mod tidy
		go mod vendor

clean:
		bash -c 'rm -f kubeexec go.mod go.sum; rm -rf vendor; true'

container-build:
		./build/container-build.sh 2>&1 | tee container-build.log


old-container-build:
		docker build -f Dockerfile -t ghcr.io/mosermichael/s9k-mm:latest . 2>&1 | tee container-build.log

.PHONY: all kubexec-no-mod build init clean container-build

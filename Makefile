
all: build-go

build-go: kubeexec
		GO111MODULE=on go build -o kubeexec github.com/MoserMichael/s9k

init:
		go mod init github.com/MoserMichael/s9k
		go mod tidy
		go mod vendor

clean:
		rm -f kubeexec || true

.PHONY: all build-go init clean

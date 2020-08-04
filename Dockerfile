# Build...
FROM golang:1.14.4-alpine3.11 AS build

RUN mkdir -p src/github.com/MoserMichael/s9k
WORKDIR ./src/github.com/MoserMichael/s9k

COPY go.mod go.sum exec.go s9k.sh s9k.py Makefile  ./
ADD ./static-file ./static-file


COPY vendor vendor 
RUN apk --no-cache add make curl && pwd && ls -al && make kubexec-no-mod  && ls -al
# -----------------------------------------------------------------------------
# Build Image...

FROM alpine:3.10.0

COPY --from=build /go/src/github.com/MoserMichael/s9k/kubeexec /bin/kubeexec
COPY --from=build /go/src/github.com/MoserMichael/s9k/s9k.py /bin/s9k.py
COPY --from=build /go/src/github.com/MoserMichael/s9k/s9k.sh /bin/s9k.sh
COPY --from=build /go/src/github.com/MoserMichael/s9k/static-file  /static-file


ENV KUBE_LATEST_VERSION="v1.18.1"

#RUN apk update \
#  && apk add --update ca-certificates \
#  && apk add --update -t deps binutils file gcc libc-dev libev python3-dev libffi-dev curl python3 py3-pip \
#  && (pip3 install -v bottle bottle-websocket || /bin/true)

RUN apk update \
  && apk add --update ca-certificates \
  && apk add --update -t deps binutils file gcc make libc-dev libev python3-dev libffi-dev curl python3 py3-pip openssl \
  && pip3 install -v bottle bottle-websocket  \
  && curl -L https://storage.googleapis.com/kubernetes-release/release/${KUBE_LATEST_VERSION}/bin/linux/amd64/kubectl -o /bin/kubectl \
  && chmod +x /bin/kubectl \
  && apk del gcc make curl \
  && rm /var/cache/apk/* 

# && apk del --purge deps py3-pip curl make gcc binutils  \

ENTRYPOINT [ "/bin/s9k.sh", "-d", "-v" ]

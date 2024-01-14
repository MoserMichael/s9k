#!/bin/bash


if [[ ! -d s9kenv ]]; then
    make initpython
    make init
    make kubeexec
fi

source s9kenv/bin/activate

python3 s9k.py






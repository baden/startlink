#!/bin/sh

# Exclude .venv and __pycache__ directories
#scp -r --exclude='.venv' --exclude='__pycache__' ./drone root@192.168.3.67:/root

#scp -r ./drone/* root@192.168.3.73:/root
scp -r ./drone/* root@luckfox.local:/root


#!/bin/sh

SERVER="baden@s.navi.cc"
DEST="~/startlink-server/"

# Створимо каталог на сервері, якщо його нема
ssh $SERVER "mkdir -p $DEST"

# scp server/*.py $SERVER:$DEST
# scp drone/*.py $SERVER:$DEST
# #scp server/requirements.txt $SERVER:$DEST

rsync server/ -r --exclude '.venv' $SERVER:$DEST

cd drone
date > version.txt
tar --disable-copyfile -czf ../drone.tar.gz .
cd ..
scp drone.tar.gz $SERVER:$DEST/s.navi.cc/
scp drone/version.txt $SERVER:$DEST/s.navi.cc/
rsync drone/ -r --exclude '__pycache__' --exclude '.vscode' $SERVER:$DEST/s.navi.cc/drone/

#!/bin/sh

SERVER="baden@s.navi.cc"
DEST="~/startlink-server/"

# Створимо каталог на сервері, якщо його нема
ssh $SERVER "mkdir -p $DEST"

# scp server/*.py $SERVER:$DEST
# scp drone/*.py $SERVER:$DEST
# #scp server/requirements.txt $SERVER:$DEST

rsync server/ -r --exclude '.venv' $SERVER:$DEST

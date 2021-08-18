#!/bin/sh

cd ./articles/

git add *
git commit -m "Adding articles and updating db"
git push origin master

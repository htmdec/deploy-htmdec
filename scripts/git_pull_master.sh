#!/bin/bash

for dir in $(find src/ -maxdepth 1 -mindepth 1 -type d | sort) ; do \
  pushd $dir &> /dev/null
  echo $dir
  git checkout -- . &> /dev/null
  git checkout master &> /dev/null
  git pull origin master &> /dev/null
  echo "${dir} updated and set to master"
  popd &> /dev/null
done

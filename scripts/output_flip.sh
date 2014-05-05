#!/bin/bash
set -o nounset
set -o errexit

contents=$(cat $1)
if [[ $contents == 'true' ]]
then
    echo dc > $1
elif [[ $contents == 'false' ]]
then
    echo notdc > $1
else
    echo 'invalid answer'
    exit 1
fi

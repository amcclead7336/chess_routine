#!/bin/bash

UNAME=$1
API_TOKEN=$2
FILE_PATH=$3
DEPLOYFILE_PATH=$4

PA_URL="https://www.pythonanywhere.com"
AUTH_HEADER="Authorization: Token $API_TOKEN"

curl -XPOST -v -F "content=@$FILE_PATH" --header "$AUTH_HEADER" $PA_URL/api/v0/user/$UNAME/files/path$DEPLOYFILE_PATH
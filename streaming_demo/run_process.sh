#!/bin/bash

set -x

PROCESS_REGISTRY_URL="http://127.0.0.1:8000"
PROCESS_DISPATCHER_URL="http://127.0.0.1:8001"
MISTER_CLUSTER_URL="http://127.0.0.1:8002"
CALLBACK_URL="http://requestb.in/1ajj2571"

echo "Testing the streaming architecture"

function extract_token {

    RESULT=$(echo $1 | sed 's/.*"token"://g' | sed 's/,.*//g' | sed 's/"//g' | sed 's/}//g')

    echo "$RESULT"
}

function extract_id {

    RESULT=$(echo $1 | sed 's/.*"id"://g' | sed 's/,.*//g')

    echo "$RESULT"
}

if [ "$1" == "" ]; then
    echo "Please provide the id of the process as a parameter"
    exit 1
fi

if [ "$2" == "" ]; then
    echo "Please provide the token required by mister cluster"
    exit 1
fi


########################################################
# RUNNING THE PROCESS
########################################################

PROCESS_ID=$1
MRCLUSTER_TOKEN=$2

read -r -d '' PROCESS_PARAMETERS_JSON_VALUE <<- EOM
{
   "parameter": "plop"
}
EOM
PROCESS_PARAMETERS_JSON_VALUE_ESCAPED=$(echo $PROCESS_PARAMETERS_JSON_VALUE | sed 's/"/\\\"/g')

read -r -d '' PROCESS_FILE_PARAMETERS_JSON_VALUE <<- EOM
{
   "input_file": "http://dropbox.jonathanpastor.fr/input.txt"
}
EOM
PROCESS_FILE_PARAMETERS_JSON_VALUE_ESCAPED=$(echo $PROCESS_FILE_PARAMETERS_JSON_VALUE | sed 's/"/\\\"/g')

read -r -d '' PROCESS_EXECUTION_JSON_VALUE <<- EOM
{
  "id": 0,
  "author": 0,
  "process_id": $PROCESS_ID,
  "parameters": "$PROCESS_PARAMETERS_JSON_VALUE_ESCAPED",
  "files": "$PROCESS_FILE_PARAMETERS_JSON_VALUE_ESCAPED",
  "callback_url": "$CALLBACK_URL",
  "output_location": "string",
  "mrcluster_token": "$MRCLUSTER_TOKEN"
}
EOM

curl -u admin:pass -X POST --header 'Content-Type: application/json' --header 'Accept: application/json' -d "$PROCESS_EXECUTION_JSON_VALUE" "$PROCESS_DISPATCHER_URL/pdapp/exec/"

exit 0

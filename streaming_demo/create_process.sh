#!/bin/bash

set -x

PROCESS_REGISTRY_URL="http://127.0.0.1:8000"
PROCESS_DISPATCHER_URL="http://127.0.0.1:8001"
MISTER_CLUSTER_URL="http://127.0.0.1:8002"
CALLBACK_URL="http://requestb.in/1mstk8z1"

echo "Testing the streaming architecture"

function extract_token {

    RESULT=$(echo $1 | sed 's/.*"token"://g' | sed 's/,.*//g' | sed 's/"//g' | sed 's/}//g')

    echo "$RESULT"
}

function extract_id {

    RESULT=$(echo $1 | sed 's/.*"id"://g' | sed 's/,.*//g')

    echo "$RESULT"
}

########################################################
# CREATION OF PROCESS
########################################################

read -r -d '' ADAPTER_JSON_VALUE <<- EOM
{
   "exec":"bash run_job.sh",
   "argv":[
      "@{input_file}",
      "parameter"
   ],
   "cwd":"~",
   "environment":{
      "ENV1":"env1",
      "ENV2":"2",
      "ENV3":"${env3}"
   },
   "output_adapter":{
      "output_type":"file",
      "output_parameters":{
         "file_path":"output.txt"
      }
   }
}
EOM
ADAPTER_JSON_VALUE_ESCAPED=$(echo $ADAPTER_JSON_VALUE | sed 's/"/\\\"/g')

read -r -d '' PROCESS_JSON_VALUE <<- EOM
{
    "name": "line_counter_hadoop",
    "author": 1,
    "appliance_id": 1,
    "archive_url": "http://dropbox.jonathanpastor.fr/archive.tgz",
    "adapters": "$ADAPTER_JSON_VALUE_ESCAPED"
}
EOM

echo $PROCESS_JSON_VALUE

PROCESS_REGISTRATION_OUTPUT=$(curl -u admin:pass -X POST --header 'Content-Type: application/json' --header 'Accept: application/json' -d "$PROCESS_JSON_VALUE" "$PROCESS_REGISTRY_URL/prapp/processdef/")
PROCESS_ID=$(extract_id $PROCESS_REGISTRATION_OUTPUT)
echo $PROCESS_ID

exit 0

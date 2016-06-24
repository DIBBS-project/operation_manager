#!/bin/bash

# set -x

PROCESS_REGISTRY_URL="http://127.0.0.1:8000"
PROCESS_DISPATCHER_URL="http://127.0.0.1:8001"
MISTER_CLUSTER_URL="http://127.0.0.1:8002"

RESOURCE_MANAGER_URL="http://127.0.0.1:8002"
APPLIANCE_REGISTRY_URL="http://127.0.0.1:8003"

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


########################################################
# CREATION OF ACTIONS
########################################################


if [ "$1" != "skip" ]; then
    read -r -d '' ACTION_JSON_VALUE <<- EOM
{
  "name": "configure_node"
}
EOM
    ACTION_REGISTRATION_OUTPUT=$(curl -u admin:pass -X POST --header 'Content-Type: application/json' --header 'Accept: application/json' -d "$ACTION_JSON_VALUE" "$APPLIANCE_REGISTRY_URL/actions/")

    read -r -d '' ACTION_JSON_VALUE <<- EOM
{
  "name": "prepare_node"
}
EOM
    ACTION_REGISTRATION_OUTPUT=$(curl -u admin:pass -X POST --header 'Content-Type: application/json' --header 'Accept: application/json' -d "$ACTION_JSON_VALUE" "$APPLIANCE_REGISTRY_URL/actions/")

    read -r -d '' ACTION_JSON_VALUE <<- EOM
{
  "name": "update_master_node"
}
EOM
    ACTION_REGISTRATION_OUTPUT=$(curl -u admin:pass -X POST --header 'Content-Type: application/json' --header 'Accept: application/json' -d "$ACTION_JSON_VALUE" "$APPLIANCE_REGISTRY_URL/actions/")

    read -r -d '' ACTION_JSON_VALUE <<- EOM
{
  "name": "user_data"
}
EOM
    ACTION_REGISTRATION_OUTPUT=$(curl -u admin:pass -X POST --header 'Content-Type: application/json' --header 'Accept: application/json' -d "$ACTION_JSON_VALUE" "$APPLIANCE_REGISTRY_URL/actions/")

    read -r -d '' ACTION_JSON_VALUE <<- EOM
{
  "name": "update_hosts_file"
}
EOM
    ACTION_REGISTRATION_OUTPUT=$(curl -u admin:pass -X POST --header 'Content-Type: application/json' --header 'Accept: application/json' -d "$ACTION_JSON_VALUE" "$APPLIANCE_REGISTRY_URL/actions/")
fi


########################################################
# CREATION OF THE APPLIANCES
########################################################

for FOLDER in appliances/*; do
    APPLIANCE_NAME=$(echo $FOLDER | sed 's/.*\///g' | sed 's/\..*//g')
    read -r -d '' APPLIANCE_JSON_VALUE <<- EOM
{
  "name": "${APPLIANCE_NAME}"
}
EOM
    curl -u admin:pass -X POST --header 'Content-Type: application/json' --header 'Accept: application/json' -d "$APPLIANCE_JSON_VALUE" "$APPLIANCE_REGISTRY_URL/appliances/"

    for FILE in $FOLDER/*; do
        ACTION_NAME=$(echo $FILE | sed 's/.*\///g' | sed 's/\..*//g')
        ESCAPED_CONTENT=$(cat $FILE | sed 's/"/\\\"/g' | sed -e ':a' -e 'N' -e '$!ba' -e 's/\n/\\n/g')
        # CONTENT=$(cat $FILE)
        # ESCAPED_CONTENT=$(printf '%q' $CONTENT)

        read -r -d '' SCRIPT_JSON_VALUE <<- EOM
{
  "code": "${ESCAPED_CONTENT}",
  "appliance": "${APPLIANCE_NAME}",
  "action": "${ACTION_NAME}"
}
EOM
        echo "============================================"
        echo "$SCRIPT_JSON_VALUE"
        echo "============================================"
        curl -u admin:pass -X POST --header 'Content-Type: application/json' --header 'Accept: application/json' -d "$SCRIPT_JSON_VALUE" "$APPLIANCE_REGISTRY_URL/scripts/"
    done
done

exit 0

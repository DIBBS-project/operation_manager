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
# CREATION OF A USER FOR OPENSTACK
########################################################

USER="jpastor"
PASSWORD="bar"
PROJECT="FG-392"

function extract_cluster_id {

    RESULT=$(echo $1 | sed 's/.*"cluster_id"://g' | sed 's/,.*//g' | sed 's/}//g')

    echo "$RESULT"
}

function extract_user_id {

    RESULT=$(echo $1 | sed 's/.*"user_id"://g' | sed 's/,.*//g' | sed 's/}//g')

    echo "$RESULT"
}

function extract_api_token {

    RESULT=$(echo $1 | sed 's/.*"api_token"://g' | sed 's/,.*//g' | sed 's/}//g')

    echo "$RESULT"
}

# Create a new user
USER_CREATION_OUTPUT=$(curl -H "Content-Type: application/json" -X POST -d "{\"username\": \"$USER\", \"project\": \"$PROJECT\", \"password\": \"$PASSWORD\"}" $RESOURCE_MANAGER_URL/users/)
USER_ID=$(extract_user_id $USER_CREATION_OUTPUT)
TOKEN=$(extract_api_token $USER_CREATION_OUTPUT)

# Upload openstack password in an encrypted way
USER_GET_OUTPUT=$(curl -H "TOKEN: $TOKEN" -X GET $RESOURCE_MANAGER_URL/users/$USER_ID/)
echo "$USER_GET_OUTPUT" | sed 's/.*"security_certificate":"//g' | sed 's/"}//g' | awk '{gsub(/\\n/,"\n")}1' > certificate.txt

set +x

echo "Please enter your OpenStack Password: "
read -sr OS_PASSWORD_INPUT

echo "$OS_PASSWORD_INPUT" > password.txt
cat password.txt | openssl rsautl -encrypt -pubin -inkey certificate.txt > cipher.txt
rm -rf password.txt

echo "=========== encrypted(password) ==========="
cat cipher.txt
echo "==========================================="

set -x

# Send the encrypted password to the webservice
curl -i -H "TOKEN: $TOKEN" -X PATCH -F 'data=@cipher.txt' $RESOURCE_MANAGER_URL/users/$USER_ID/

echo "MRCLUSTER_TOKEN: $TOKEN"

exit 0

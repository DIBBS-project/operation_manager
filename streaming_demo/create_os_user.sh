#!/bin/bash

# set -x

RESOURCE_MANAGER_URL="http://127.0.0.1:8002"
PASSWORD="bar"

########################################################
# CREATION OF A USER FOR OPENSTACK
########################################################

function extract_user_id {

    RESULT=$(echo $1 | sed 's/.*"user_id"://g' | sed 's/,.*//g' | sed 's/}//g')

    echo "$RESULT"
}

function extract_api_token {

    RESULT=$(echo $1 | sed 's/.*"api_token"://g' | sed 's/,.*//g' | sed 's/}//g')

    echo "$RESULT"
}


if [ "$#" -ne 2 ]; then
    if [ "$#" -ne 3 ]; then
        echo "Usage: $0 <username> <project> [<resource manager URL>]"
        exit 1
    fi
fi

USER=$1
PROJECT=$2
if [ "$#" -ne 2 ]; then
    RESOURCE_MANAGER_URL=$3
fi


# Create a new user
echo "Creating user \"$USER\" with project \"$PROJECT\"..."

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

# set -x

# Send the encrypted password to the webservice
curl -i -H "TOKEN: $TOKEN" -X PATCH -F 'data=@cipher.txt' $RESOURCE_MANAGER_URL/users/$USER_ID/

# echo "MRCLUSTER_TOKEN: $TOKEN"
echo ""

exit 0

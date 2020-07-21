#!/bin/bash
#set -x

PATH=/use/your/PATH/here

export http_proxy=http://proxy.com/
export https_proxy=http://proxy.com/

# PARAMS
NAME="NAME"
REPO=repo/dhis2-data
INSTANCE=2.30-ANY-INSTANCE
PORT=8080
DEPLOY_PATH="deploy-path"
TOMCAT_SERVER_XML_PATH=/your/path/to/server.xml

TIMESTAMP=$(date)

check_args(){
    echo ""
    if [ $# -eq 5 ]; then
        REPO=$1
        INSTANCE=$2
        PORT=$3
        DEPLOY_PATH=$4
        TOMCAT_SERVER_XML_PATH=$5
        echo "using provided parameters:"
    else
        echo "no parameter provided or incorrect parameters number. Please remember to provide all of them and in the following order 1) repo 2) instance 3) port 4) deploy path 5) tomcat server xml path. By default values are:"
    fi
    echo "repo: ${REPO}"
    echo "instance: ${INSTANCE}"
    echo "port: ${PORT}"
    echo "deploy path: ${DEPLOY_PATH}"
    echo "tomcat server xml path: ${TOMCAT_SERVER_XML_PATH}"
    echo ""
    echo ""
}

check_status(){
    if [ $? -eq 0 ]; then
        echo OK
    else
        echo FAIL
    fi
}

welcome_message(){
    echo ""
    echo ""
    echo ">>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>"
    echo "[$TIMESTAMP] -- INSTANCE REBOOT -- START"
    echo ">>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>"
}

goodbye_message(){
    echo "<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<"
    echo "[$TIMESTAMP] -- INSTANCE REBOOT -- END"
    echo "<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<"
    echo ""
}

set_timestamp(){
    TIMESTAMP=$(date)
}

set_timestamp
welcome_message

check_args

echo "instance reboot - applying action (stop, pull, start)"

echo "stopping ${REPO}:${INSTANCE}..."
d2-docker stop "${REPO}:${INSTANCE}"
check_status
echo ""

echo "pulling ${REPO}:${INSTANCE}..."
d2-docker pull "${REPO}:${INSTANCE}"
check_status
echo ""

echo "starting ${REPO}:${INSTANCE} --port=${PORT} --detach --deploy-path ${DEPLOY_PATH} --tomcat-server-xml ${TOMCAT_SERVER_XML_PATH}..."
d2-docker start "${REPO}:${INSTANCE}" --port="${PORT}" --detach --deploy-path "${DEPLOY_PATH}" --tomcat-server-xml "${TOMCAT_SERVER_XML_PATH}"
check_status
echo ""

set_timestamp
goodbye_message

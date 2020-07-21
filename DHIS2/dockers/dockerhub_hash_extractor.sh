#!/bin/bash
#set -x

PATH=/use/your/PATH/here

export DOCKER_USERNAME=username
export DOCKER_PASSWORD=pass
export http_proxy=http://proxy.com/
export https_proxy=http://proxy.com/

# PARAMS
NAME="NAME"
REPO=repo/dhis2-data
INSTANCE=2.30-ANY-INSTANCE
OUTPUT_FOLDER=/your/output/folder
OUTPUT_FILE=output_file.txt
PORT=8080
DEPLOY_PATH="deploy-path"
TOMCAT_SERVER_XML_PATH=/your/path/to/server.xml
ESTOOlS_PATH=/your/path/to/ESTools

TIMESTAMP=$(date)

check_args(){
    echo ""
    if [ $# -eq 7 ]; then
        REPO=$1
        INSTANCE=$2
        OUTPUT_FOLDER=$3
        OUTPUT_FILE=$4
        PORT=$5
        DEPLOY_PATH=$6
        TOMCAT_SERVER_XML_PATH=$7
        echo "using provided parameters:"
    else
        echo "no parameter provided or incorrect parameters number. Please remember to provide all of them and in the following order 1) repo 2) instance 3) output folder 4) output file 5) port 6) deploy path 7) tomcat server xml path. By default values are:"
    fi
    echo "repo: ${REPO}"
    echo "instance: ${INSTANCE}"
    echo "output folder: ${OUTPUT_FOLDER}"
    echo "output file: ${OUTPUT_FILE}"
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
    echo "[$TIMESTAMP] -- INSTANCE HASH EXTRACTOR -- START"
    echo ">>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>"
}

goodbye_message(){
    echo "<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<"
    echo "[$TIMESTAMP] -- INSTANCE HASH EXTRACTOR -- END"
    echo "<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<"
    echo ""
}

set_timestamp(){
    TIMESTAMP=$(date)
}

set_timestamp
welcome_message

check_args

echo "checking previous hash..."
current_instance=$(cat "${OUTPUT_FOLDER}/${OUTPUT_FILE}" | jq .instance)
current_hash=$(cat "${OUTPUT_FOLDER}/${OUTPUT_FILE}" | jq .hash)
echo "instance: $current_instance"
echo "current hash: $current_hash"
echo ""

echo "updating hash for ${INSTANCE} in ${OUTPUT_FOLDER}/${OUTPUT_FILE}"
/bin/bash ${ESTOOLS_PATH}/DHIS2/dockers/get-image-config.sh $REPO $INSTANCE 2>/dev/null | jq '. | {instance: "'"${NAME}"'", hash: .Hostname}' > ${OUTPUT_FOLDER}/${OUTPUT_FILE}
check_status
echo ""

new_instance=$(cat "${OUTPUT_FOLDER}/${OUTPUT_FILE}" | jq .instance)
new_hash=$(cat "${OUTPUT_FOLDER}/${OUTPUT_FILE}" | jq .hash)
echo "instance: $new_instance"
echo "new hash: $new_hash"
echo ""

if [[ "$current_hash" != "$new_hash" ]]; then
    echo "instance modification detected - applying action (stop, pull, start)"

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
else
    echo "no modification detected"
fi

set_timestamp
goodbye_message

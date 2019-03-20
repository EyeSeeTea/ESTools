#!/bin/bash
set -euo pipefail
alias aspera=~/.aspera/cli/bin/aspera 

REMOTE_HOST="fileshare.rediris.es"
REMOTE_USER="adrian@eyeseetea.com"
ROOT_LOCAL_FOLDER="$HOME/data"
ROOT_REMOTE_FOLDER='/CNB/CNBPROYECTO1/CBNSHARE'

syncPath(){
        local remote_folder=$1
        local local_data=$2
        #Get ls with formatted dates and ordered by time
        local local_files=$(TZ=utc ls $local_data -altr --color=auto \
         --time-style=full-iso)

        #Get filenames column
        local local_filenames=$(echo "$local_files" | awk '{print $9}')

        #Get aspera folder info and remove all less files table
        local result=$(aspera shares browse -i -u $REMOTE_USER \
        --host $REMOTE_HOST --path=$remote_folder --sort mtime_a \
        | sed -n  '/----/,/----/p' |sed '$d;1d;2d' )

        echo "$result" |
        while IFS= read -r aspera_row;do
                #Get aspera item values
                local filename=$(echo $aspera_row | awk '{print $4}')
                local size=$(echo $aspera_row | awk '{print $2}')
                local type=$(echo $aspera_row | awk '{print $1}')
                local date=$(echo $aspera_row | awk '{print $3}')

                #Get and convert ls and aspera dates to timestamp
                local local_file=$(echo "$local_files" \
                | sed -n '/'"$filename"'$/p')
                if ! [ -z "$local_file" ];then
                        #format ls date to timestamp
                        local local_date=$(echo $local_file | awk '{print $6}')
                        local local_hour=$(echo $local_file | awk '{print $7}')
                        local_date=$(echo $local_date$local_hour | \
                        cut -f1 -d".")
                        local local_file_timestamp=$(busybox date -u \
                        -d $local_date +%s -D  %Y-%m-%d%H:%M:%S)
                fi
                #format aspera item date to timestamp
                local file_timestamp=$(busybox date -u \
                -d $date +%s -D %Y-%m-%dT%H:%M:%SZ)

                #Check if the filename exist in the local filenames,
                #and if the creation date is before than server updated date
                if [[ "$local_filenames" == *"$filename"* ]] && \
                [[ $file_timestamp -lt local_file_timestamp ]];then
                        echo "Already exist: $filename"
                #Ignore files with 0kb.
                elif [ $size == 0 -a ${type:0:1} == "-" ]
                then
                        echo "Ignore File with 0kb: $filename"
                else
                        echo "Start download: $filename"
                        aspera shares download -i -u $REMOTE_USER \
                        --host $REMOTE_HOST --source=$remote_folder/$filename \
                         --destination=$local_data
                fi
        done

}

syncPath $ROOT_REMOTE_FOLDER $ROOT_LOCAL_FOLDER

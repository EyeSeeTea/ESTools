#!/bin/bash
set -euo pipefail
alias aspera=~/.aspera/cli/bin/aspera 

REMOTE_HOST="fileshare.rediris.es"
REMOTE_USER="adrian@eyeseetea.com"
ROOT_LOCAL_FOLDER="$HOME/data"
ROOT_REMOTE_FOLDER='/CNB/CNBPROYECTO1/CBNSHARE'

syncPath(){
        REMOTE_FOLDER=$1
        LOCAL_DATA=$2
        #Get ls with formatted dates and ordered by time
        lslist=`TZ=utc ls $LOCAL_DATA -altr --color=auto --time-style=full-iso`

        #Get filenames column
        localfilenames=`echo "$lslist" | awk '{print $9}'`

        #Get aspera folder info and remove all less files table
        result=`aspera shares browse -i -u $REMOTE_USER --host $REMOTE_HOST --path=$REMOTE_FOLDER  --sort mtime_a | sed -n  '/----/,/----/p' | sed '$d;1d;2d' `

        echo "$result" |
        while IFS= read -r asperarow;do
                #Get aspera item values
                filename=`echo $asperarow | awk '{print $4}'`
                size=`echo $asperarow | awk '{print $2}'`
                type=`echo $asperarow | awk '{print $1}'`
                date=`echo $asperarow | awk '{print $3}'`

                #Get and convert ls and aspera dates to timestamp
                lsfilerow=`echo "$lslist" | sed -n '/'"$filename"'$/p'`
                if ! [ -z "$lsfilerow" ];then
                        localdate=`echo $lsfilerow | awk '{print $6}'`
                        localhour=`echo $lsfilerow | awk '{print $7}'`
                        localdate=`echo $localdate$localhour | cut -f1 -d"."`
                        localfiledate=`busybox date -u -d $localdate -D %Y-%m-%d%H:%M:%S`
                        localfiledate=`date -d "$localfiledate" +%s`
                fi
                filedate=`busybox date -u -d $date -D %Y-%m-%dT%H:%M:%SZ`
                filedate=`date -d "$filedate" +%s`

                #Check if the filename exist in the local filenames, and if the creation date is before than the server updated date
                if [[ "$localfilenames" == *"$filename"* ]] && [[ $filedate -lt $localfiledate ]]; then
                        echo "Already exist: $filename"
                #Ignore files with 0kb.
                elif [ $size == 0 -a ${type:0:1} == "-" ]
                then
                        echo "Ignore File with 0kb: $filename"
                else
                        echo "Start download: $filename"
                        aspera shares download -i -u $REMOTE_USER --host $REMOTE_HOST --source=$REMOTE_FOLDER/$filename --destination=$LOCAL_DATA
                fi
        done

}

syncPath $ROOT_REMOTE_FOLDER $ROOT_LOCAL_FOLDER

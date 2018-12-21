FROM ubuntu:18.04

RUN apt-get update && apt-get install -y apt-utils && apt-get install -y openssh-server screen netcat rsync vim
RUN sed -i "s/RSYNC_ENABLE=false/RSYNC_ENABLE=true/" /etc/default/rsync
COPY rsyncd.conf /etc

EXPOSE 22
EXPOSE 873

ENTRYPOINT service ssh start && service rsync start && tail -f /dev/null

## Setup

$ ssh -L 9000:localhost:80 root@wdb13.cnb.csic.es

- Access web interface in http://localhost:9000
- Install app "abFiles" (Apps -> App store)

## Setup

$ scp cnb-start.sh root@wdb13.cnb.csic.es:
$ ssh root@wdb13.cnb.csic.es
$ cp cnb-start.sh /mnt/HD/HD_a2/Nas_Prog/abFiles/
$ chmod +x cnb-start.sh /mnt/HD/HD_a2/Nas_Prog/abFiles/cnb-start.sh
$ echo "/mnt/HD/HD_a2/Nas_Prog/abFiles/cnb-start.sh" >> /mnt/HD/HD_a2/Nas_Prog/abFiles/init.sh

### Docker

## Setup

$ docker -t internal_system:versionN build docker
$ docker run --name backstabbing_feynman -p 8000:22/tcp -p 873:873/tcp -v /mnt/nas:/mnt -td internal_system:versionN

## Start

$ docker start backstabbing_feynman

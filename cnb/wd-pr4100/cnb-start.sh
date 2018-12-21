#!/bin/sh

setup() {
    # Docker
    docker_image="backstabbing_feynman"
    docker start $docker_image
    docker exec -t $docker_image /etc/init.d/ssh start
    docker exec -t $docker_image /etc/init.d/rsync start

    # Re-create LVM /dev/mapper entries
    lvm vgchange -a y

    # Mount stardard PR4100 mountpoints to avoid breaking things the web interface
    mount /dev/vg/pr4100-hd-b2 /mnt/HD/HD_b2/
    mount /dev/vg/pr4100-hd-c2 /mnt/HD/HD_c2/
    mount /dev/vg/pr4100-hd-d2 /mnt/HD/HD_d2/

    # Custom mounts (mountpoints: one line per file: name of LV and directory)
    mountpoints_path="/mnt/HD/HD_a2/Nas_Prog/abFiles/mountpoints"
    mkdir -p /mnt/nas
    cat "$mountpoints_path" | grep '[^[:space:]]' | while read name; do
      mkdir -p /mnt/nas/$name
      mount /dev/vg/$name /mnt/nas/$name
    done
}

# Give some time for the docker daemon to start
(sleep 1m && setup) &

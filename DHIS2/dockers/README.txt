# script to check dockerhub hash

Usage:
- For private repos
DOCKER_USERNAME=user DOCKER_PASSWORD=password ./get-image-config.sh repo/image tag

- For public repos
./get-image-config.sh repo/image tag

- Get only json output and store it in a file
DOCKER_USERNAME=user DOCKER_PASSWORD=password ./get-image-config.sh repo/image tag 2>/dev/null

- Build new json file with selected properties
DOCKER_USERNAME=user DOCKER_PASSWORD=password ./get-image-config.sh repo/image tag 2>/dev/null | jq '. | {instance: "INSTANCE", hash: .Hostname}'


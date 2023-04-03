#!/bin/sh

domain=htmdec.org
role=manager,celery
image=wholetale/gwvolman:latest
registry_user=fido
registry_pass=secretpass
r2d_version=wholetale/repo2docker_wholetale:latest
matlab_file_installation_key=$MATLAB_KEY
node_id=$(docker info --format "{{.Swarm.NodeID}}")
celery_args="-Q ${role},${node_id} --hostname=${node_id} -c 3"

docker stop -t 0 celery_worker >/dev/null 2>&1
docker rm celery_worker > /dev/null 2>&1

# docker pull ${image} > /dev/null 2>&1
# Do not set GIRDER_API_URL for celery_worker it's handled elsewhere for local deployment
# See my comment: https://github.com/whole-tale/deploy-dev/issues/10#issuecomment-451193663

docker run \
    --name celery_worker \
    --label traefik.enable=false \
    -e GOSU_USER=wtuser:1000:$(getent group docker | cut -d: -f3) \
    -e DOMAIN=${domain} \
    -e DEV=true \
    -e REPO2DOCKER_VERSION="${r2d_version}" \
    -e TRAEFIK_NETWORK=wt_traefik-net \
    -e TRAEFIK_ENTRYPOINT=websecure \
    -e REGISTRY_USER=${registry_user} \
    -e REGISTRY_URL=https://registry.${domain} \
    -e REGISTRY_PASS=${registry_pass} \
    -e WT_LICENSE_PATH=/srv/hemi01-j01/htmdec/wt_volumes/licenses \
    -e WT_VOLUMES_PATH=/srv/hemi01-j01/htmdec/wt_volumes \
    -e MATLAB_FILE_INSTALLATION_KEY=${matlab_file_installation_key} \
    -v /var/run/docker.sock:/var/run/docker.sock:ro \
    -v /tmp:/tmp \
    -v $PWD/src/gwvolman:/gwvolman \
    -v $PWD/src/girderfs:/girderfs \
    --mount type=bind,source="/srv/hemi01-j01/htmdec/wt_volumes",target="/srv/hemi01-j01/htmdec/wt_volumes",bind-propagation=rshared \
    --device /dev/fuse \
    --cap-add SYS_ADMIN \
    --security-opt apparmor:unconfined \
    --network wt_celery \
    -d ${image} ${celery_args}

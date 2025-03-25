ssh-add ~/.ssh/id_rsa
DOCKER_BUILDKIT=1 docker build --ssh default -t video_upload_workflow .

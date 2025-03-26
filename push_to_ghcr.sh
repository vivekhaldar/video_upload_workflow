# Push latest image to GitHub Container Registry.

docker tag video_upload_workflow:latest ghcr.io/vivekhaldar/video_upload_workflow:latest
pass dev/GITHUB_PAT_GHCR | docker login ghcr.io -u vivekhaldar --password-stdin
docker push ghcr.io/vivekhaldar/video_upload_workflow:latest
